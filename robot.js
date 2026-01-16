<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robot Rond Mignon 3D</title>
    <style>
        /* Pour l'exemple autonome, on garde le plein écran */
        body { margin: 0; overflow: hidden; background-color: #87CEEB; }
        #info {
            position: absolute; top: 10px; width: 100%;
            text-align: center; color: white; font-family: sans-serif;
            font-weight: bold; pointer-events: none; text-shadow: 1px 1px 2px black;
        }
    </style>
</head>
<body>
    <div id="info">Le nouveau robot à tête ronde !</div>

    <script type="importmap">
        {
            "imports": {
                "three": "https://unpkg.com/three@0.160.0/build/three.module.js"
            }
        }
    </script>

    <script type="module">
        import * as THREE from 'three';

        // --- CONFIGURATION ---
        // C'est ici qu'on décidera où s'affiche le robot (voir Partie 2 des explications)
        // Si on ne trouve pas de conteneur spécifique, on utilise la fenêtre entière.
        const container = document.getElementById('robot-container') || document.body;
        
        let width = container.clientWidth || window.innerWidth;
        let height = container.clientHeight || window.innerHeight;
        // Si le conteneur a une hauteur de 0 (bug fréquent), on force une hauteur
        if (height === 0) height = 400; 

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xaaccff);
        
        // Caméra un peu plus proche pour le nouveau look
        const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
        camera.position.set(0, 1.5, 7);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = true;
        // IMPORTANT : On attache le canvas au conteneur choisi, pas juste au body
        container.appendChild(renderer.domElement);

        // Lumières
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        scene.add(ambientLight);
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // --- CRÉATION DU ROBOT ROND ---
        const robotGroup = new THREE.Group();
        
        // Matériaux
        const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 });
        const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.3 });
        const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
        const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 });

        // --- NOUVELLE TÊTE RONDE ---
        const headRadius = 0.7;
        // SphereGeometry(rayon, segmentsLargeur, segmentsHauteur)
        const headGeo = new THREE.SphereGeometry(headRadius, 32, 32);
        const head = new THREE.Mesh(headGeo, whiteMat);
        head.castShadow = true;
        
        // Écran (Visage noir) - Légèrement incurvé ou juste placé devant
        const faceGeo = new THREE.CircleGeometry(0.55, 32);
        const face = new THREE.Mesh(faceGeo, darkMat);
        // On le positionne juste à la surface de la sphère (rayon 0.7)
        face.position.set(0, 0, headRadius + 0.02);
        head.add(face);

        // Yeux
        const eyeGeo = new THREE.CircleGeometry(0.12, 32);
        const leftEye = new THREE.Mesh(eyeGeo, glowMat);
        leftEye.position.set(-0.25, 0.1, headRadius + 0.05);
        const rightEye = new THREE.Mesh(eyeGeo, glowMat);
        rightEye.position.set(0.25, 0.1, headRadius + 0.05);
        head.add(leftEye); 
        head.add(rightEye);

        // Sourire
        const smileGeo = new THREE.TorusGeometry(0.15, 0.03, 16, 100, Math.PI);
        const smile = new THREE.Mesh(smileGeo, glowMat);
        smile.rotation.z = Math.PI;
        smile.position.set(0, -0.15, headRadius + 0.05);
        head.add(smile);

        // Antenne (position ajustée pour le haut de la sphère)
        const antStickGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.3);
        const antStick = new THREE.Mesh(antStickGeo, blueMat);
        antStick.position.y = headRadius - 0.1;
        head.add(antStick);
        const antBallGeo = new THREE.SphereGeometry(0.15);
        const antBall = new THREE.Mesh(antBallGeo, blueMat);
        antBall.position.y = headRadius + 0.2;
        head.add(antBall);

        // Corps (Un peu plus arrondi aussi)
        const bodyGeo = new THREE.CylinderGeometry(0.4, 0.55, 0.
