import * as THREE from 'three';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };
// IMPORTANT : Si le robot réussit à passer en plein écran total, 
// il faudra descendre un peu plus le haut du cadre pour ne pas être SUR le titre.
// Essayons 0.20 (20% de marge haute)
const TOP_OFFSET_PERCENT = 0.20; 

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

// --- INIT : L'ÉVASION ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', escapeAndLaunch);
} else {
    escapeAndLaunch();
}

function escapeAndLaunch() {
    // 1. NETTOYAGE TOTAL
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-canvas-escape'];
    oldIds.forEach(id => {
        // On cherche dans la fenêtre actuelle ET la fenêtre parente au cas où
        const el = document.getElementById(id);
        if (el) el.remove();
        try {
            if (window.top.document) {
                const elTop = window.top.document.getElementById(id);
                if (elTop) elTop.remove();
            }
        } catch(e){}
    });

    // 2. CRÉATION DU CANVAS
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-escape';
    
    // 3. LA CIBLE : LE VRAI BODY
    // On essaie d'atteindre le "window.top.document.body" (le chef suprême de la page)
    let targetBody = document.body;
    let isTopLevel = false;

    try {
        if (window.top && window.top.document && window.top.document.body) {
            targetBody = window.top.document.body;
            isTopLevel = true;
            console.log("🚀 ÉVASION RÉUSSIE : Robot attaché au Body Principal !");
        }
    } catch (e) {
        console.warn("🔒 ÉVASION BLOQUÉE (Cross-Origin) : On reste dans le cadre local.");
    }

    targetBody.appendChild(canvas);

    // 4. STYLE ULTRA FORCÉ
    canvas.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 2147483647 !important;
        pointer-events: none !important;
        background: transparent !important; /* PLUS DE VERT */
        display: block !important;
        transform: none !important;
        margin: 0 !important;
        padding: 0 !important;
    `;

    initThreeJS(canvas, isTopLevel);
}

function initThreeJS(canvas, isTopLevel) {
    // Si on est sur le top level, on utilise window.top pour les dimensions
    const targetWindow = isTopLevel ? window.top : window;
    
    let width = targetWindow.innerWidth;
    let height = targetWindow.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(targetWindow.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 1 : CADRE ROUGE ---
    // =========================================================
    let updateBorderFunc = () => {};

    if (config.mode === 'photos') {
        const borderGeo = new THREE.BufferGeometry();
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 3 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        scene.add(borderLine);

        function getPointAtZ0(ndcX, ndcY, camera) {
            const vector = new THREE.Vector3(ndcX, ndcY, 0.5);
            vector.unproject(camera);
            vector.sub(camera.position).normalize();
            const distance = -camera.position.z / vector.z;
            return new THREE.Vector3().copy(camera.position).add(vector.multiplyScalar(distance));
        }

        updateBorderFunc = () => {
            const w = targetWindow.innerWidth;
            const h = targetWindow.innerHeight;
            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();

            const topNDC = 1.0 - (TOP_OFFSET_PERCENT * 2);
            // On se met à 100% (1.0)
            const limit = 1.0; 

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

    // BULLE DE TEXTE (Attachement au bon endroit)
    const bubbleId = 'robot-bubble-escape';
    let bubbleOverlay = targetWindow.document.getElementById(bubbleId);
    if (!bubbleOverlay) {
        bubbleOverlay = targetWindow.document.createElement('div');
        bubbleOverlay.id = bubbleId;
        bubbleOverlay.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 15px 25px; border-radius: 30px; font-family: sans-serif; font-weight: bold; font-size: 18px;
            pointer-events: none; z-index: 2147483647; transition: opacity 0.3s;
        `;
        targetBody.appendChild(bubbleOverlay);
    }

    // ANIMATION
    let time = 0;
    robotGroup.position.set(0, -1, 0);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        robotGroup.position.y = -1 + Math.sin(time) * 0.1;

        if(bubbleOverlay && bubbleOverlay.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); 
            headPos.y += 0.8; 
            headPos.project(camera);
            const x = (headPos.x * .5 + .5) * targetWindow.innerWidth; 
            const y = (headPos.y * -.5 + .5) * targetWindow.innerHeight;
            bubbleOverlay.style.left = Math.max(0, Math.min(targetWindow.innerWidth - 200, x)) + 'px';
            bubbleOverlay.style.top = (y - 80) + 'px';
        }
        renderer.render(scene, camera);
    }

    targetWindow.addEventListener('resize', () => {
        const w = targetWindow.innerWidth;
        const h = targetWindow.innerHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        if(config.mode === 'photos') updateBorderFunc();
    });

    animate();
}
