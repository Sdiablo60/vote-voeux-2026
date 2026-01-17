import * as THREE from 'three';

// =========================================================
// 🔴 RÉGLAGE ASCENSEUR (Y) 🔴
// =========================================================
// 0 = Milieu de l'écran.
// 5.0 = Haut de l'écran (Visible).
// 6.5 = Bordure extrême du haut.
//
// CONSIGNES :
// 1. Lancez avec 5.0 -> Vous verrez la ligne.
// 2. Si elle est trop basse : Augmentez (ex: 5.5, 6.0, 6.2...)
// 3. Si elle est trop haute : Diminuez (ex: 4.5)
const POSITION_Y_LIGNE = 6.7; 

// Largeur (1.0 = normal)
const FACTEUR_LARGEUR = 1.0; 
// =========================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibrationOnly);
} else {
    launchCalibrationOnly();
}

function launchCalibrationOnly() {
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer', 'live-container'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-calibration-layer';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 2147483647 !important; pointer-events: none !important;
        background: transparent !important;
    `;

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

    // CADRE ROUGE
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 5 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        // --- CALCUL DES LIMITES POUR LA LARGEUR ---
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;
        const halfW = visibleWidth / 2;

        // --- POSITIONNEMENT MANUEL (ASCENSEUR) ---
        // On utilise directement votre chiffre
        const yTop = POSITION_Y_LIGNE;
        
        // Le bas est symétrique ou forcé vers le bas (-6.0)
        const yBottom = -6.0; 
        
        const xRight = halfW * FACTEUR_LARGEUR;   
        const xLeft = -xRight;   

        const points = [
            new THREE.Vector3(xLeft, yTop, 0),
            new THREE.Vector3(xRight, yTop, 0),
            new THREE.Vector3(xRight, yBottom, 0),
            new THREE.Vector3(xLeft, yBottom, 0)
        ];
        borderGeo.setFromPoints(points);
    }

    updateBorder();

    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        updateBorder();
    });
}
