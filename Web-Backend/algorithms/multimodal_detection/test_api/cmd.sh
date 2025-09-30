curl -X POST http://localhost:5001/predict -H "Content-Type: application/json" -d '{"task_id": "rhfx-001", "url": "", "data_id": "001", "type": ""}'

curl -X POST http://localhost:5001/predict -H "Content-Type: application/json" -d '{"task_id": "rhfx-001", "text_url": "BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs", "image_url": "/home/lihr/finally_project/multimodal_detection/test_api/fake_news.png"}'


curl -X POST http://localhost:5017/api/multimodal/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs", "image_url": "/home/lihr/finally_project/multimodal_detection/test_api/fake_news.png"}'