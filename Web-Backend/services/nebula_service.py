# /unified_service/services/search_service.py

import logging
import os
import time
from towhee import AutoPipes, AutoConfig
from towhee.datacollection import DataCollection
from pymilvus import MilvusClient
from elasticsearch import Elasticsearch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
from imagehash import phash
import numpy as np

logger = logging.getLogger(__name__)

# 全局客户端变量
es_client = None
milvus_client = None

def init_search_clients(app_config):
    """初始化Elasticsearch和Milvus客户端"""
    global es_client, milvus_client
    
    # 初始化Elasticsearch
    try:
        es_client = Elasticsearch(
            hosts=app_config.get('ES_HOSTS'),
            basic_auth=app_config.get('ES_AUTH')
        )
        if es_client.ping():
            logger.info('连接Elasticsearch成功!')
            count = es_client.cat.count(index=app_config.get('ES_INDEX'), format="json")[0]['count']
            logger.info(f"ES索引 '{app_config.get('ES_INDEX')}' 中当前文档总数: {count}")
        else:
            raise ConnectionError("连接Elasticsearch失败")
    except Exception as e:
        logger.error(f"初始化Elasticsearch客户端时出错: {e}")
        exit(1)

    # 初始化Milvus
    try:
        milvus_client = MilvusClient(uri=app_config.get('MILVUS_URI'), token=app_config.get('MILVUS_TOKEN'))
        logger.info("连接Milvus成功!")
    except Exception as e:
        logger.error(f"初始化Milvus客户端时出错: {e}")
        exit(1)

# --- 文本搜索逻辑 ---

def _compute_ngram_similarity(query_text, doc_texts, n=3):
    all_texts = [query_text] + doc_texts
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(n, n), lowercase=False)
    try:
        vectors = vectorizer.fit_transform(all_texts)
        sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        return sims.tolist()
    except ValueError:
        return [0.0] * len(doc_texts)

def search_text(query_content, score_threshold, app_config, top_k_first=100, ngram_n=3):
    """两阶段文本搜索：ES召回 + n-gram重排序"""
    if not es_client:
        raise ConnectionError("Elasticsearch客户端未初始化")

    search_body = {
        "query": {"match": {"content": query_content}},
        "_source": ["id", "title", "content", "publishtime", "event", "uid", "uname", 
                    "isrumor", "datasource", "istweet", "isretweet", "retext", "pic_ids", "pic_urls"],
        "size": top_k_first
    }
    
    try:
        response = es_client.search(index=app_config.get('ES_INDEX'), body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return []

        candidates = [hit["_source"] for hit in hits]
        candidate_contents = [c["content"] for c in candidates]
        
        similarities = _compute_ngram_similarity(query_content, candidate_contents, n=ngram_n)
        
        for c, sim in zip(candidates, similarities):
            c["ngram_sim"] = sim
            c["isSource"] = -1

        candidates = [c for c in candidates if c["ngram_sim"] > score_threshold]

        for c in candidates:
            if c.get("datasource") == 'weibo':
                if c["istweet"] and not c["isretweet"]:  
                # if c.get("istweet") == "true" and c.get("isretweet") == "false":
                    c["isSource"] = 0
            else:
                c["isSource"] = 0

        id_group = {}
        for c in candidates:
            id_val = c.get("event")
            if id_val not in id_group:
                id_group[id_val] = []
            id_group[id_val].append(c)
        
        temp_candidates = []
        for group in id_group.values():
            # sorted_group = sorted(group, key=lambda x: x.get("publishtime", ""), reverse=False)
            # sorted_group = sorted(group, key=lambda x: x["ngram_sim"], reverse=True)
            sorted_group = sorted(group, key=lambda x: x["publishtime"], reverse=False)
            found_source = False
            for item in sorted_group:
                if not found_source and item["isSource"] == 0:
                    item["isSource"] = 1
                    found_source = True
            # for item in sorted_group:
            #     if item["isSource"] == -1:
            #         item["isSource"] = 0
            temp_candidates.extend(sorted_group)

        id_group = {}
        for c in candidates:
            id_val = c.get("datasource")
            if id_val not in id_group:
                id_group[id_val] = []
            id_group[id_val].append(c)
        
        final_candidates = []
        for group in id_group.values():
            # sorted_group = sorted(group, key=lambda x: x.get("publishtime", ""), reverse=False)
            # sorted_group = sorted(group, key=lambda x: x["ngram_sim"], reverse=True)
            sorted_group = sorted(group, key=lambda x: x["publishtime"], reverse=False)
            found_source = False
            for item in sorted_group:
                if not found_source and (item["isSource"] == 0 or item["isSource"] == 1):
                    item["isSource"] = 1
                    found_source = True
            for item in sorted_group:
                if item["isSource"] == -1:
                    item["isSource"] = 0
            final_candidates.extend(sorted_group)
        
        for c in candidates:
            c["imageUrl"] = c.pop("pic_urls", -1)  # 使用 pop 删除原键并获取其值 重命名       

        return final_candidates

    except Exception as e:
        logger.error(f"文本搜索出错: {e}")
        return {"error": str(e)}

# --- 图像搜索逻辑 ---

def _convert_bool_list_to_bytes(bool_list):
    byte_array = bytearray(len(bool_list) // 8)
    for i, bit in enumerate(bool_list):
        if bit:
            byte_array[i // 8] |= (1 << (i % 8))
    return bytes(byte_array)

def _calculate_phash_signature(image_file, hash_size=16):
    pil_image = Image.open(image_file).convert("L").resize(
        (hash_size + 1, hash_size), Image.Resampling.LANCZOS
    )
    phash_value = phash(pil_image, hash_size)
    pil_image.close()
    
    bool_array = phash_value.hash.flatten()
    bit_array = bool_array.astype(np.uint8)
    return _convert_bool_list_to_bytes(bit_array)

def search_picture(image_path, app_config):
    """使用Milvus进行图像pHash搜索"""
    if not milvus_client:
        raise ConnectionError("Milvus客户端未初始化")
    
    try:
        img_hash = _calculate_phash_signature(image_path)
        results = milvus_client.search(
            collection_name=app_config.get('MILVUS_IMAGE_COLLECTION'),
            data=[img_hash],
            output_fields=["data_path","mid"]
        )
        results = [[hit for hit in result_list if hit["distance"] < 90] for result_list in results]
        print(results)
        
        pred_paths = []
        pred_mid = []
        for result_set in results:
            top_n_paths = [item["entity"]["data_path"] for item in result_set]
            pred_paths.append(top_n_paths)
            top_n_mid = [item["entity"]["mid"] for item in result_set]
            pred_mid.append(top_n_mid)
            
        return pred_paths,pred_mid
        
    except Exception as e:
        logger.error(f"图像搜索出错: {e}")
        return {"error": str(e)}


def search_event_by_mid(query_content, app_config, top_k_first=1, ngram_n=3):
    """两阶段文本搜索：ES召回 + n-gram重排序"""
    if not es_client:
        raise ConnectionError("Elasticsearch客户端未初始化")

    search_body = {
        "query": {"term": {"id": query_content}},
        "_source": ["id", "title", "content", "publishtime", "event", "uid", "uname", 
                    "isrumor", "datasource", "istweet", "isretweet", "retext", "pic_ids", "pic_urls"],
        "size": top_k_first
    }
    
    try:
        response = es_client.search(index=app_config.get('ES_INDEX'), body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return []

        candidates = [hit["_source"] for hit in hits]
        candidate_contents = [c["content"] for c in candidates]
        
        similarities = _compute_ngram_similarity(query_content, candidate_contents, n=ngram_n)
        
        for c, sim in zip(candidates, similarities):
            c["ngram_sim"] = sim
            c["isSource"] = -1

        for c in candidates:
            if c.get("datasource") == 'weibo':
                if c["istweet"] and not c["isretweet"]:  
                # if c.get("istweet") == "true" and c.get("isretweet") == "false":
                    c["isSource"] = 0
            else:
                c["isSource"] = 0

        id_group = {}
        for c in candidates:
            id_val = c.get("event")
            if id_val not in id_group:
                id_group[id_val] = []
            id_group[id_val].append(c)
        
        temp_candidates = []
        for group in id_group.values():
            # sorted_group = sorted(group, key=lambda x: x.get("publishtime", ""), reverse=False)
            # sorted_group = sorted(group, key=lambda x: x["ngram_sim"], reverse=True)
            sorted_group = sorted(group, key=lambda x: x["publishtime"], reverse=False)
            found_source = False
            for item in sorted_group:
                if not found_source and item["isSource"] == 0:
                    item["isSource"] = 1
                    found_source = True
            # for item in sorted_group:
            #     if item["isSource"] == -1:
            #         item["isSource"] = 0
            temp_candidates.extend(sorted_group)
        id_group = {}
        for c in candidates:
            id_val = c.get("datasource")
            if id_val not in id_group:
                id_group[id_val] = []
            id_group[id_val].append(c)
        
        final_candidates = []
        for group in id_group.values():
            # sorted_group = sorted(group, key=lambda x: x.get("publishtime", ""), reverse=False)
            # sorted_group = sorted(group, key=lambda x: x["ngram_sim"], reverse=True)
            sorted_group = sorted(group, key=lambda x: x["publishtime"], reverse=False)
            found_source = False
            for item in sorted_group:
                if not found_source and (item["isSource"] == 0 or item["isSource"] == 1):
                    item["isSource"] = 1
                    found_source = True
            for item in sorted_group:
                if item["isSource"] == -1:
                    item["isSource"] = 0
            final_candidates.extend(sorted_group)
        
        for c in candidates:
            c["imageUrl"] = c.pop("pic_urls", -1)  # 使用 pop 删除原键并获取其值 重命名       

        return final_candidates

    except Exception as e:
        logger.error(f"图片搜索出错: {e}")
        return {"error": str(e)}

# --- 视频搜索逻辑 ---

def search_video(video_path, score, app_config):
    """使用Towhee和Milvus进行视频拷贝检测"""
    try:
        search_conf = AutoConfig.load_config('video_copy_detection')
        search_conf.collection = app_config.get('MILVUS_VIDEO_COLLECTION')
        search_conf.milvus_host = app_config.get('MILVUS_URI').split('//')[1].split(':')[0]
        search_conf.milvus_port = int(app_config.get('MILVUS_URI').split(':')[-1])
        search_conf.device = app_config.get('TOWHEE_DEVICE')
        search_conf.leveldb_path = app_config.get('TOWHEE_LEVELDB_PATH')
        search_conf.threshold = score
        
        search_pipe = AutoPipes.pipeline('video_copy_detection', search_conf)
        results = search_pipe(video_path)
        res = DataCollection(results).to_list()
        
        # 假设返回结果是每个检测段的候选视频列表，我们这里简化为只取第一个结果的候选列表
        res_value = [r['candidates'] for r in res] if res else []
        print(res_value)
        return res_value
        # 将多个候选列表拍平并去重
        # flat_unique_list = []
        # if res_value:
        #      seen = set()
        #      for sublist in res_value[0]:
        #          if sublist not in seen:
        #              seen.add(sublist)
        #              flat_unique_list.append(sublist)
        # return flat_unique_list

    except Exception as e:
        logger.error(f"视频搜索出错: {e}")
        return {"error": str(e)}