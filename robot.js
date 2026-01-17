import * as THREE from 'three';

// On ignore le container HTML existant qui est piégé.
// On va en créer un nouveau dynamiquement.

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };
const TOP_OFFSET_PERCENT = 0.18; // Marge du haut pour le titre

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

// --- CRÉATION FORCEE DU CALQUE (GHOST LAYER) ---
function createFullscreenLayer() {
    const layerId = 'robot-ghost-layer';
    let layer = document.getElementById(layerId);
    
    if (!layer) {
        layer = document.createElement('div');
        layer.id = layerId;
        // On l'ajoute tout à la fin du body, hors de toute structure existante
        document.body.appendChild(layer);
    }

    // Styles incompressibles pour garantir le plein écran
    layer.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 2147483647 !important; /* Maximum possible */
        pointer-events: none !important;
        background: transparent !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    `;

    return layer;
}

// On lance le processus
const ghostContainer = createFullscreenLayer();
initRobot(ghostContainer);


// --- LE CODE DU ROBOT ---
function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    const scene = new THREE.Scene();
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    // Important : on s'assure que le fond est transparent
    renderer.setClearColor(0x000000, 0); 
    
    // On vide le container avant d'ajouter le canvas
    while (container.firstChild) container.removeChild(container.firstChild);
    container.appendChild(renderer.domElement);

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 1 : CADRE ROUGE (SUR LE GHOST LAYER) ---
    // =========================================================
    let updateDebugBorder = () => {}; 

    if (config.mode === 'photos') {
        const borderGeo = new THREE.BufferGeometry();
        // Ligne très épaisse (4px)
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        scene.add(borderLine);

        function getPointAtZ0(ndcX, ndcY, camera) {
            const vector = new THREE.Vector3(ndcX, ndcY, 0.5);
            vector.unproject(camera);
            vector.sub(camera.position).normalize();
            const distance = -camera.position.z / vector.z;
            return new THREE.Vector3().copy(camera.position).add(vector.multiplyScalar(distance));
        }

        updateDebugBorder = () => {
            // Re-forcer la taille du renderer au cas où
            renderer.setSize(window.innerWidth, window.innerHeight);
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();

            const topNDC = 1.0 - (TOP_OFFSET_PERCENT * 2);
            // On utilise 0.995 pour être sûr de voir le trait
            const limit = 0.995; 

            const pTL = getPointAtZ0(-limit, topNDC, camera); 
            const pTR = getPointAtZ0(limit, topNDC, camera);  
            const pBR = getPointAtZ0(limit, -limit, camera);    
            const pBL = getPointAtZ0(-limit, -limit, camera);   

            const points = [pTL, pTR, pBR, pBL, pTL];
            borderGeo.setFromPoints(points);
        };
        updateDebugBorder(); 
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

    // --- ANIMATION ---
    let time = 0;
    // Position : Centré horizontalement, un peu bas (-1)
    let targetPosition = new THREE.Vector3(0, -1, 0); 
    robotGroup.position.copy(targetPosition);

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;
        
        // Petit mouvement de vie pour confirmer qu'il marche
        robotGroup.position.y = -1 + Math.sin(time) * 0.1;
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.1;

        renderer.render(scene, camera);
    }

    // Gestion redimensionnement
    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        if(config.mode === 'photos') updateDebugBorder();
    });

    animate();
}
