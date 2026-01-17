import * as THREE from 'three';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };
const TOP_OFFSET_PERCENT = 0.18; 

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

// --- INIT FORCÉE ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', forceLayerCreation);
} else {
    forceLayerCreation();
}

function forceLayerCreation() {
    // 1. DIAGNOSTIC IFRAME (Regardez la console F12)
    if (window.self !== window.top) {
        console.warn("ALERTE : LE ROBOT EST COINCÉ DANS UNE IFRAME !");
        console.warn("Il ne pourra pas sortir de ce cadre sans modifier le site parent.");
    }

    // 2. NETTOYAGE AGRESSIF
    // On supprime tout ce qui pourrait s'appeler robot-container
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer'];
    oldIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.remove();
    });

    // 3. CRÉATION TOILE NEUVE
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    
    // 4. ATTACHEMENT RACINE (HTML au lieu de BODY)
    document.documentElement.appendChild(canvas);

    // 5. STYLES "TOP PRIORITÉ"
    canvas.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 2147483647 !important;
        pointer-events: none !important;
        background: rgba(255, 0, 0, 0.5) !important; /* FOND ROUGE TEMPORAIRE */
        display: block !important;
        transform: none !important;
    `;

    // 6. FLASH DIAGNOSTIC
    // Le fond rouge disparaît après 1 seconde si tout va bien
    setTimeout(() => {
        canvas.style.background = 'transparent';
    }, 1000);

    initThreeJS(canvas);
}

function initThreeJS(canvas) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 1 : CADRE ROUGE (SUR TOUT L'ÉCRAN) ---
    // =========================================================
    let updateBorderFunc = () => {};

    if (config.mode === 'photos') {
        const borderGeo = new THREE.BufferGeometry();
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 5 });
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
            // Forçage des dimensions
            const w = window.innerWidth;
            const h = window.innerHeight;
            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();

            const topNDC = 1.0 - (TOP_OFFSET_PERCENT * 2);
            // On utilise 0.999 pour coller aux bords
            const limit = 0.999; 

            const pTL = getPointAtZ0(-limit, topNDC, camera); 
            const pTR = getPointAtZ0(limit, topNDC, camera);  
            const pBR = getPointAtZ0(limit, -limit, camera);    
            const pBL = getPointAtZ0(-limit, -limit, camera);   

            const points = [pTL, pTR, pBR, pBL, pTL];
            borderGeo.setFromPoints(points);
        };
        // Exécution immédiate et répétée pour contrer les chargements dynamiques
        updateBorderFunc();
        setTimeout(updateBorderFunc, 500);
        setInterval(updateBorderFunc, 2000); // Vérification continue
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

    // BULLE DE TEXTE
    let bubbleOverlay = document.getElementById('robot-bubble-force');
    if (!bubbleOverlay) {
        bubbleOverlay = document.createElement('div');
        bubbleOverlay.id = 'robot-bubble-force';
        bubbleOverlay.style.cssText = `
            position: fixed; opacity: 0; background: white; color: black;
            padding: 15px 25px; border-radius: 30px; font-family: sans-serif; font-weight: bold; font-size: 18px;
            pointer-events: none; z-index: 2147483647; transition: opacity 0.3s;
        `;
        document.body.appendChild(bubbleOverlay);
    }

    // ANIMATION
    let time = 0;
    robotGroup.position.set(0, -1, 0);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        robotGroup.position.y = -1 + Math.sin(time) * 0.1;
        
        // Suivi bulle
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

    window.addEventListener('resize', () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        if(config.mode === 'photos') updateBorderFunc();
    });

    animate();
}
