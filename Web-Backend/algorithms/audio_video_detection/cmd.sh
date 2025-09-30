# 测试音频文件
curl -X POST http://localhost:5014/api/audiovideo/detect \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/lihr/Key_Research/add_flfx-003/FaceForensics/classification/test/audio_and_video/Bye-bye.wav"}'

# 测试视频文件
curl -X POST http://localhost:5014/api/audiovideo/detect \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/lihr/Key_Research/add_flfx-003/FaceForensics/classification/test/audio_and_video/1aJO2VkfZiY_2_EMLALfhSftA_0.mp4"}'