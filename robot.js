import * as THREE from 'three';

// On récupère la config, mais on ignore le conteneur HTML qui nous piège
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

// --- INIT : ON S'ATTACHE AU BODY DIRECTEMENT ---
// On lance le robot dès que possible
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchOverlayRobot);
} else {
    launchOverlayRobot();
}

function launchOverlayRobot() {
    // 1. Nettoyage : On supprime l'ancien container piégé s'il existe
    const oldContainer = document.getElementById('robot-container');
    if (oldContainer) oldContainer.style.display = 'none'; // On le cache

    // 2. Création de notre propre toile (Canvas)
    // On vérifie si elle existe déjà pour ne pas la dupliquer
    let canvas = document.getElementById('robot-canvas-overlay');
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.id = 'robot-canvas-overlay';
        document.body.appendChild(canvas); // ON LE COLLE SUR LE BODY DIRECTEMENT
    }

    // 3. Styles CSS forcés (Impossible d'être piégé ici)
    canvas.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important; /* Tout en haut */
        pointer-events: none !important; /* Clics traversants */
        background: transparent !important;
        display: block !important;
    `;

    // 4. Initialisation 3D sur ce canvas
    initThreeJS(canvas);
}

function initThreeJS(canvas) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    // RENDERER (On utilise notre canvas forcé)
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0); // Transparent

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 1 : CADRE ROUGE (TEST FINAL) ---
    // =========================================================
    // Réglage : 0.18 = Laisser de la place en haut pour le titre
    const TOP_OFFSET_PERCENT = 0.18; 

    // Variable globale pour la mise à jour
    let updateBorderFunc = () => {};

    if (config.mode === 'photos') {
        const borderGeo = new THREE.BufferGeometry();
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        scene.add(borderLine);

        // Fonction mathématique de projection inverse
        function getPointAtZ0(ndcX, ndcY, camera) {
            const vector = new THREE.Vector3(ndcX, ndcY, 0.5);
            vector.unproject(camera);
            vector.sub(camera.position).normalize();
            const distance = -camera.position.z / vector.z;
            return new THREE.Vector3().copy(camera.position).add(vector.multiplyScalar(distance));
        }

        updateBorderFunc = () => {
            const topNDC = 1.0 - (TOP_OFFSET_PERCENT * 2);
            // On utilise 0.99 pour être sûr d'être visible
            const limit = 0.99; 

            const pTL = getPointAtZ0(-limit, topNDC, camera); 
            const pTR = getPointAtZ0(limit, topNDC, camera);  
            const pBR = getPointAtZ0(limit, -limit, camera);    
            const pBL = getPointAtZ0(-limit, -limit, camera);   

            const points = [pTL, pTR, pBR, pBL, pTL];
            borderGeo.setFromPoints(points);
        };
        updateBorderFunc();
    }
    // =========================================================

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.7, 0.7, 0.7);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData = { origPos: new THREE.Vector3(x, y, z), origRot: new THREE.Euler(0, 0, 0) };
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head).scale.set(1.25, 0.85, 0.6);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI;
    const lEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head); lEar.rotation.z = Math.PI/2;
    const rEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head); rEar.rotation.z = Math.PI/2;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body).rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup); leftArm.rotation.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup); rightArm.rotation.z = -0.15;

    scene.add(robotGroup);

    // BULLE DE TEXTE (Recréée dynamiquement aussi pour éviter les pièges)
    let bubbleOverlay = document.getElementById('robot-bubble-overlay');
    if (!bubbleOverlay) {
        bubbleOverlay = document.createElement('div');
        bubbleOverlay.id = 'robot-bubble-overlay';
        bubbleOverlay.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 15px 25px; border-radius: 30px; font-family: sans-serif; font-weight: bold; font-size: 18px;
            pointer-events: none; z-index: 1000000; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: opacity 0.3s;
        `;
        // Petite flèche de bulle
        const arrow = document.createElement('div');
        arrow.style.cssText = "position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 8px solid transparent; border-right: 8px solid transparent; border-top: 8px solid white;";
        bubbleOverlay.appendChild(arrow);
        document.body.appendChild(bubbleOverlay);
    }

    // --- ANIMATION ---
    let time = 0;
    // Position : Centré horizontalement, un peu bas (-1)
    let targetPosition = new THREE.Vector3(0, -1, 0); 
    robotGroup.position.copy(targetPosition);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        
        // Mouvement de vie
        robotGroup.position.y = -1 + Math.sin(time) * 0.1;
        
        // Suivi Bulle
        if(bubbleOverlay && bubbleOverlay.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); 
            headPos.y += 0.8; 
            headPos.project(camera);
            const x = (headPos.x * .5 + .5) * window.innerWidth; 
            const y = (headPos.y * -.5 + .5) * window.innerHeight;
            bubbleOverlay.style.left = (x - bubbleOverlay.offsetWidth / 2) + 'px';
            bubbleOverlay.style.top = (y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); 
        camera.aspect = width / height; 
        camera.updateProjectionMatrix();
        if(config.mode === 'photos') updateBorderFunc();
    });

    animate();
}
