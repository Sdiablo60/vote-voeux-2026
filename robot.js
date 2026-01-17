import * as THREE from 'three';

// --- CONFIGURATION ---
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

// --- INIT SÉCURISÉE (SANS SORTIE IFRAME) ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLocalLayer);
} else {
    initLocalLayer();
}

function initLocalLayer() {
    // 1. NETTOYAGE
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-canvas-escape'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // 2. CSS RESET SUR LA FRAME LOCALE
    document.documentElement.style.cssText = "margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%;";
    document.body.style.cssText = "margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%;";

    // 3. CRÉATION CANVAS
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 9999; pointer-events: none; background: transparent;
    `;

    initThreeJS(canvas);
}

function initThreeJS(canvas) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    // CAMÉRA (Reculée à 14 pour bien voir les bords)
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 2 : LE POINT DE DÉPART (LA CIBLE VERTE) ---
    // =========================================================
    
    // Cadre Rouge (Pour repère)
    if (config.mode === 'photos') {
        // 1. Le Cadre Rouge
        const borderGeo = new THREE.BufferGeometry();
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        scene.add(borderLine);

        // 2. La Source (Point Vert)
        const sourceGeo = new THREE.SphereGeometry(0.5, 32, 32);
        const sourceMat = new THREE.MeshBasicMaterial({ color: 0x00FF00 });
        const sourceMesh = new THREE.Mesh(sourceGeo, sourceMat);
        scene.add(sourceMesh);

        // FONCTION DE CALCUL DES BORDS
        const updateLayout = () => {
            const w = window.innerWidth;
            const h = window.innerHeight;
            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();

            const dist = camera.position.z;
            const vFOV = THREE.MathUtils.degToRad(camera.fov);
            const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
            const visibleWidth = visibleHeight * camera.aspect;

            // Limites 3D exactes
            const topY = visibleHeight / 2;
            const rightX = visibleWidth / 2;

            // --- RÉGLAGE HAUTEUR DE LA SOURCE ---
            // On place la boule verte tout en haut (Y = topY)
            // On décale légèrement vers le bas (-0.5) pour qu'elle soit visible
            sourceMesh.position.set(0, topY - 0.5, 0);

            // Mise à jour du cadre rouge
            const pTL = new THREE.Vector3(-rightX, topY, 0);
            const pTR = new THREE.Vector3(rightX, topY, 0);
            const pBR = new THREE.Vector3(rightX, -topY, 0);
            const pBL = new THREE.Vector3(-rightX, -topY, 0);
            borderGeo.setFromPoints([pTL, pTR, pBR, pBL, pTL]);
        };

        updateLayout();
        window.addEventListener('resize', updateLayout);
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

    // Position initiale
    let targetPosition = new THREE.Vector3(0, -1, 0); 
    robotGroup.position.copy(targetPosition);

    // BULLE TEXTE (Recréée pour être sûr)
    let bubbleOverlay = document.getElementById('robot-bubble-force');
    if (!bubbleOverlay) {
        bubbleOverlay = document.createElement('div');
        bubbleOverlay.id = 'robot-bubble-force';
        bubbleOverlay.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 15px 25px; border-radius: 30px; font-family: sans-serif; font-weight: bold; font-size: 18px;
            pointer-events: none; z-index: 10000; transition: opacity 0.3s;
        `;
        document.body.appendChild(bubbleOverlay);
    }

    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        robotGroup.position.y = -1 + Math.sin(time) * 0.1;
        
        if(bubbleOverlay && bubbleOverlay.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); 
            headPos.y += 0.8; 
            headPos.project(camera);
            const x = (headPos.x * .5 + .5) * window.innerWidth; 
            const y = (headPos.y * -.5 + .5) * window.innerHeight;
            bubbleOverlay.style.left = Math.max(0, Math.min(window.innerWidth - 200, x)) + 'px';
            bubbleOverlay.style.top = (y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }
    animate();
}
