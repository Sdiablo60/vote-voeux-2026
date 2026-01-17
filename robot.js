import * as THREE from 'three';

// =========================================================
// 🔴 CORRECTION MANUELLE VERTICALE (FORCE BRUTE) 🔴
// =========================================================
// Mettez une valeur positive pour FORCER le trait à remonter.
// Essayez 0.5 pour commencer.
// Si c'est trop haut, baissez (0.3). Si trop bas, montez (0.8).
const FORCE_MONTEE = 1.5; 

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
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    function updateBorder() {
        const dist = camera.position.z;
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // CALCUL : On prend le haut de l'écran et on AJOUTE votre force de montée
        // Si FORCE_MONTEE = 0.5, on remonte le trait de 0.5 unités virtuelles au-dessus du "top" mathématique.
        const yTop = halfH + FORCE_MONTEE; 
        
        const yBottom = -halfH + 0.5; // On remonte un peu le bas aussi pour qu'il soit visible
        const xRight = halfW;   
        const xLeft = -halfW;   

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
