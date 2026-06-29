
print('Loading faster-whisper base...')
from faster_whisper import WhisperModel
m1 = WhisperModel('base', device='cpu', compute_type='int8')
print('  base model: OK')

print('Loading sentence-transformer...')
from sentence_transformers import SentenceTransformer
m2 = SentenceTransformer('all-MiniLM-L6-v2')
vec = m2.encode('test sentence')
print(f'  embedding model: OK (vector size: {len(vec)})')

print()
print('All AI models pre-loaded and cached. Future startups will be fast.')
