import * as THREE from 'three';

// =========================================================================
// 🔴 ZONE DE RÉGLAGE - MODIFIEZ CES 3 CHIFFRES UNIQUEMENT 🔴
// =========================================================================

// 1. HAUTEUR (Pour descendre la ligne du haut sous votre titre)
// Plus le chiffre est grand, plus la ligne DESCEND.
// Essayez : 1.5, 2.0, 2.5...
const MARGE_HAUT = 2.2; 

// 2. BAS (Pour remonter la ligne du bas si elle est cachée)
// Plus le chiffre est grand, plus la ligne REMONTE.
// Essayez : 0.0 (tout en bas), 0.5, 1.0...
const MARGE_BAS = 0.0;

// 3. LARGEUR (Pour écarter les bords gauche/droite)
// 1.0 = Largeur mathématique exacte.
// Si vous voyez des bandes noires, mettez 1.0.
// Si les lignes sortent de l'écran, mettez 0.95.
const FACTEUR_LARGEUR = 1.0; 

// =========================================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchCalibration);
} else {
    launchCalibration();
}

function launchCalibration() {
    // NETTOYAGE TOTAL (On supprime tout ancien robot)
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-canvas-escape'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // CRÉATION DU CALQUE DE CALIBRAGE
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-calibration-layer';
    document.body.appendChild(canvas);

    // STYLE FORCÉ (PLEIN ÉCRAN)
    canvas.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 2147483647 !important;
        pointer-events: none !important;
        background: transparent !important;
    `;

    initThreeJS(canvas);
}

function initThreeJS(canvas) {
    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    // CAMÉRA FIXE À Z=14
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0); // Transparent

    // --- LE CADRE DE CALIBRAGE ---
    const borderGeo = new THREE.BufferGeometry();
    // Ligne rouge très visible
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 4 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    // Fonction de calcul précis
    function updateBorder() {
        const dist = camera.position.z; // 14
        const vFOV = THREE.MathUtils.degToRad(camera.fov); // 50 deg en rad
        
        // Hauteur et Largeur totales visibles à Z=0
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // APPLICATION DES MARGES (Celles que vous réglez en haut)
        const yTop = halfH - MARGE_HAUT;       // On descend le haut
        const yBottom = -halfH + MARGE_BAS;    // On remonte le bas
        const xRight = halfW * FACTEUR_LARGEUR; // On ajuste la largeur
        const xLeft = -xRight;

        const points = [
            new THREE.Vector3(xLeft, yTop, 0),    // Haut Gauche
            new THREE.Vector3(xRight, yTop, 0),   // Haut Droite
            new THREE.Vector3(xRight, yBottom, 0),// Bas Droite
            new THREE.Vector3(xLeft, yBottom, 0)  // Bas Gauche
        ];
        borderGeo.setFromPoints(points);
    }

    updateBorder();

    // Boucle de rendu simple
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    // Mise à jour si on redimensionne la fenêtre
    window.addEventListener('resize', () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        updateBorder();
    });
}
