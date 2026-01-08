import * as THREE from 'three';

// --- INITIALISATION ---
const container = document.getElementById('robot-container');

if (container) {
    initRobot(container);
}

function initRobot(container) {
    let width = container.clientWidth;
    let height = container.clientHeight;
    if (height === 0) height = 500;

    // SCÈNE
    const scene = new THREE.Scene();
    // Pas de couleur de fond (transparent) pour aller avec ton site noir
    // scene.background = new THREE.Color(0xaaccff); 

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1.5, 7);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // ROBOT
    const robotGroup = new THREE.Group();
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Tête
    const headGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const head = new THREE.Mesh(headGeo, whiteMat);
    
    // Visage
    const faceGeo = new THREE.CircleGeometry(0.55, 32);
    const face = new THREE.Mesh(faceGeo, darkMat);
    face.position.set(0, 0, 0.71);
    head.add(face);

    // Yeux
    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.73);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.73);
    head.add(leftEye); head.add(rightEye);

    // Corps
    const bodyGeo = new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32);
    const body = new THREE.Mesh(bodyGeo, whiteMat);
    body.position.y = -0.9;

    // Bras
    function createArm(x) {
        const g = new THREE.Group();
        g.position.set(x, -0.7, 0);
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.2), blueMat);
        g.add(s);
        const a = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5), whiteMat);
        a.position.y = -0.3;
        g.add(a);
        return g;
    }
    const leftArm = createArm(-0.6);
    const rightArm = createArm(0.6);

    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(leftArm);
    robotGroup.add(rightArm);
    robotGroup.position.y = 0.5;
    scene.add(robotGroup);

    // ANIMATION
    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.05;
        
        // Flottement
        robotGroup.position.y = 0.5 + Math.sin(time) * 0.1;
        // Coucou bras droit
        rightArm.rotation.z = Math.cos(time * 3) * 0.5 + 0.5;
        
        renderer.render(scene, camera);
    }
    
    // Redimensionnement
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    });

    animate();
}import * as THREE from 'three';

// --- INITIALISATION ---
// On cherche l'élément HTML qui doit contenir le robot
const container = document.getElementById('robot-container');

// Si le conteneur existe, on lance le robot. Sinon, on ne fait rien pour éviter les bugs.
if (container) {
    initRobot(container);
}

function initRobot(container) {
    // Récupère la taille de la boîte (div)
    let width = container.clientWidth;
    let height = container.clientHeight;

    // S'assurer que la boîte a une hauteur (sinon on force 400px)
    if (height === 0) height = 400;

    // --- 1. SCÈNE & CAMÉRA ---
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xaaccff); // Couleur de fond (Bleu Ciel)
    
    // Caméra
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1.5, 7); // Position de la caméra (x, y, z)

    // Rendu
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    
    // Ajoute le rendu (canvas) dans la boîte HTML
    container.appendChild(renderer.domElement);

    // --- 2. LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 10, 7);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // --- 3. CRÉATION DU ROBOT ROND ---
    const robotGroup = new THREE.Group();
    
    // Matériaux (Couleurs et textures)
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.3 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); // Yeux brillants
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 }); // Écran noir

    // TÊTE (Sphère)
    const headRadius = 0.7;
    const headGeo = new THREE.SphereGeometry(headRadius, 32, 32);
    const head = new THREE.Mesh(headGeo, whiteMat);
    head.castShadow = true;
    
    // VISAGE (Disque noir)
    const faceGeo = new THREE.CircleGeometry(0.55, 32);
    const face = new THREE.Mesh(faceGeo, darkMat);
    face.position.set(0, 0, headRadius + 0.02); // Juste devant la tête
    head.add(face);

    // YEUX
    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, headRadius + 0.05);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, headRadius + 0.05);
    head.add(leftEye); 
    head.add(rightEye);

    // SOURIRE
    const smileGeo = new THREE.TorusGeometry(0.15, 0.03, 16, 100, Math.PI);
    const smile = new THREE.Mesh(smileGeo, glowMat);
    smile.rotation.z = Math.PI;
    smile.position.set(0, -0.15, headRadius + 0.05);
    head.add(smile);

    // ANTENNES
    const antStickGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.3);
    const antStick = new THREE.Mesh(antStickGeo, blueMat);
    antStick.position.y = headRadius - 0.1;
    head.add(antStick);
    
    const antBallGeo = new THREE.SphereGeometry(0.15);
    const antBall = new THREE.Mesh(antBallGeo, blueMat);
    antBall.position.y = headRadius + 0.2;
    head.add(antBall);

    // CORPS (Cylindre arrondi)
    const bodyGeo = new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32);
    const body = new THREE.Mesh(bodyGeo, whiteMat);
    body.position.y = -0.9;
    body.castShadow = true;

    // BRAS (Fonction pour créer les bras gauche et droit)
    function createArm(isLeft) {
        const armGroup = new THREE.Group();
        const shoulder
