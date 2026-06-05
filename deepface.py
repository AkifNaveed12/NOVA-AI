"""
MOCK MODULE — DeepFace
Provides offline face embeddings using MediaPipe FaceMesh.
Fully compliant with deepface API signature.
"""
import os
import numpy as np

CANONICAL_FACE_LANDMARKS = [
    0.094308,
    0.249668,
    0.013826,
    0.000000,
    0.000000,
    0.000000,
    -0.003757,
    -0.078389,
    0.009923,
    0.125185,
    0.415285,
    0.025822,
    0.128463,
    0.434261,
    0.027752,
    0.157395,
    0.632541,
    -0.036641,
    -0.270497,
    -0.060888,
    0.751082,
    -0.069105,
    0.354408,
    0.107446,
    -0.366769,
    -0.179718,
    0.797735,
    -0.040264,
    -0.385690,
    0.529550,
    -0.115208,
    0.584235,
    0.251889,
    -0.089021,
    0.564784,
    0.221647,
    -0.057612,
    0.534564,
    0.192959,
    -0.302797,
    -0.367071,
    0.732458,
    -0.078083,
    -0.466222,
    0.560512,
    -0.032583,
    -0.178598,
    0.622626,
    -0.152423,
    -0.090748,
    0.633575,
    0.177799,
    1.239177,
    -0.086738,
    -0.177849,
    -0.175245,
    0.660348,
    -0.299357,
    0.435059,
    1.228191,
    -0.261593,
    -0.083105,
    0.725987,
    0.623730,
    -0.372690,
    0.429932,
    0.290898,
    0.253161,
    -0.004406,
    0.678549,
    -0.561632,
    0.433627,
    0.195138,
    -0.497687,
    0.446921,
    0.432895,
    0.421657,
    0.046263,
    0.402674,
    0.420143,
    0.045955,
    0.357461,
    0.411992,
    0.038830,
    0.479361,
    -0.681863,
    0.463552,
    0.187376,
    -0.596077,
    0.469078,
    0.337790,
    -0.303004,
    0.475009,
    0.473086,
    -0.302728,
    0.393657,
    0.424058,
    -0.295629,
    0.412050,
    0.464996,
    -0.396548,
    0.418821,
    1.127836,
    0.025700,
    0.701561,
    0.595454,
    -0.381976,
    0.418135,
    0.119281,
    -0.805319,
    0.754944,
    0.105643,
    -0.666944,
    0.634492,
    0.100535,
    -0.501458,
    0.508784,
    0.103144,
    -0.407627,
    0.464821,
    0.101839,
    -0.332504,
    0.427633,
    0.080376,
    -0.288161,
    0.342561,
    0.712275,
    1.130234,
]

class DeepFace:
    @staticmethod
    def build_model(model_name):
        return None

    @staticmethod
    def represent(img_path, model_name="Facenet", enforce_detection=True, detector_backend="opencv"):
        import cv2
        import mediapipe as mp
        
        # Load image
        if isinstance(img_path, str):
            if not os.path.exists(img_path):
                raise ValueError(f"File not found: {img_path}")
            img = cv2.imread(img_path)
        else:
            img = img_path
            
        if img is None:
            raise ValueError("Invalid image input or failed to load image.")
            
        # Convert BGR to RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Run FaceMesh
        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as face_mesh:
            results = face_mesh.process(rgb)
            if not results.multi_face_landmarks:
                if enforce_detection:
                    raise ValueError("No face detected in image.")
                else:
                    return [{"embedding": [0.0]*128}]
            
            landmarks = results.multi_face_landmarks[0].landmark
            pts = np.array([[l.x, l.y, l.z] for l in landmarks])
            
            # Origin at nose tip
            origin = pts[1]
            pts_centered = pts - origin
            
            # Scale by eye distance
            scale = np.linalg.norm(pts[33] - pts[263])
            if scale == 0: scale = 1.0
            pts_normalized = pts_centered / scale
            
            key_indices = [
                0, 1, 4, 13, 14, 17, 33, 39, 46, 55, 61, 78, 95, 105, 107, 133, 145, 152, 159, 234, 246,
                263, 269, 276, 285, 291, 308, 324, 334, 336, 362, 374, 380, 386, 454, 466, 10, 151, 9, 8, 168, 6
            ]
            key_pts = pts_normalized[key_indices]
            embedding = key_pts.flatten() # 126 values
            
            # Aspect ratios
            width = np.linalg.norm(pts[234] - pts[454])
            height = np.linalg.norm(pts[10] - pts[152])
            ratio1 = width / height if height != 0 else 1.0
            
            nose_to_chin = np.linalg.norm(pts[1] - pts[152])
            nose_to_forehead = np.linalg.norm(pts[1] - pts[10])
            ratio2 = nose_to_chin / nose_to_forehead if nose_to_forehead != 0 else 1.0
            
            embedding = np.append(embedding, [ratio1, ratio2])
            
            # Displacement from canonical face landmarks
            displacement = embedding - np.array(CANONICAL_FACE_LANDMARKS)
            
            # Map cosine similarity space so that similarity thresholds match Facenet:
            # Let's normalize the displacement to unit length so that cosine similarity can be calculated on it directly.
            # But wait: if we just return the displacement directly, its cosine similarity is computed in modules/face_auth.py!
            # So returning `displacement` is perfect because `modules/face_auth.py` will compute the cosine similarity
            # between `stored_displacement` and `new_displacement`!
            return [{"embedding": list(displacement)}]
