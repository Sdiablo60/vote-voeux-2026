import * as THREE from 'three';

// =========================================================
// 🟢 CALIBRAGE AUTOMATIQUE (BASÉ SUR APP.PY) 🟢
// =========================================================
// Dans votre app.py, le titre fait height: 12vh (12% de l'écran).
// On applique exactement la même valeur ici.
const HAUTEUR_TITRE_POURCENTAGE = 0.12; 

// =========================================================

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?", "Installez-vous"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !", "On partage !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- INITIALISATION ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchFinalScene);
} else {
    launchFinalScene();
}

function launchFinalScene() {
    // 1. NETTOYAGE
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    // 2. CRÉATION CANVAS PLEIN ÉCRAN
    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 10; /* Derrière le titre (999999) mais devant le fond */
        pointer-events: none !important;
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
    renderer.setClearColor(0x000000, 0); // Fond transparent

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- GROUPE DES LASERS ---
    // =========================================================
    const lasers = [];
    const sourceGroup = new THREE.Group();
    scene.add(sourceGroup);

    // Initialisation des 12 Lasers
    const colors = [0x00FF00, 0x00FFFF, 0x0055FF, 0xFF00FF, 0xFFFF00, 0xFF3300, 0xFFFFFF];
    
    if (config.mode === 'photos') {
        for(let i=0; i<12; i++) { 
            const color = colors[Math.floor(Math.random()*colors.length)];
            
            // Rayon
            const beam = new THREE.Mesh(
                new THREE.CylinderGeometry(0.04, 0.04, 1, 8, 1, true),
                new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false })
            );
            beam.rotateX(Math.PI / 2);
            beam.geometry.translate(0, 0.5, 0); // Pivot au début
            scene.add(beam);

            // Impact au sol
            const dot = new THREE.Mesh(
                new THREE.CircleGeometry(0.5, 16),
                new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, side: THREE.DoubleSide })
            );
            dot.rotation.x = -Math.PI / 2;
            scene.add(dot);

            lasers.push({
                beam: beam, dot: dot,
                targetPos: new THREE.Vector3(0, -4, 0),
                currentPos: new THREE.Vector3(0, -4, 0),
                speed: 0.02 + Math.random() * 0.03,
                isActive: false
            });
        }
    }

    // =========================================================
    // --- CALCUL DE POSITIONNEMENT (LE COEUR DU SYSTÈME) ---
    // =========================================================
    const updateLayout = () => {
        const dist = camera.position.z; 
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        
        // Dimensions totales vues par la caméra
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const halfH = visibleHeight / 2;

        // CALCUL : On descend du haut de l'écran d'exactement 12% (taille du titre)
        // Le point de départ (yStart) est donc à la jonction exacte.
        const yStart = halfH - (visibleHeight * HAUTEUR_TITRE_POURCENTAGE);
        
        // On place la source des lasers ici
        sourceGroup.position.set(0, yStart, 0);
    };
    updateLayout();

    // =========================================================
    // --- ROBOT ---
    // =========================================================
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.7, 0.7, 0.7);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        if(parent) parent.add(mesh);
        return mesh;
    }

    // Tête
    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head).scale.set(1.25, 0.85, 0.6);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head); // Yeux
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI;
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head).rotation.z = Math.PI/2; // Oreilles
    createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head).rotation.z = Math.PI/2;

    // Corps
    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body).rotation.x = Math.PI/2;

    // Bras
    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup); leftArm.rotation.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup); rightArm.rotation.z = -0.15;

    scene.add(robotGroup);
    
    // Position initiale robot (Plus bas pour laisser la place aux lasers)
    let targetPosition = new THREE.Vector3(0, -2.5, 0); 
    robotGroup.position.copy(targetPosition);

    // =========================================================
    // --- ANIMATION LOOP ---
    // =========================================================
    let time = 0;
    
    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;
        
        // Robot qui flotte doucement
        robotGroup.position.y = -2.5 + Math.sin(time * 1.5) * 0.15;
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.1;

        // Animation des Lasers
        if (config.mode === 'photos') {
            const activeCount = lasers.filter(l => l.isActive).length;
            
            lasers.forEach(l => {
                // Gestion Aléatoire ON/OFF
                if(Math.random() > 0.98) {
                    if(l.isActive) l.isActive = false; 
                    else if(activeCount < 8) { // Max 8 lasers simultanés
                        l.isActive = true;
                        
                        // Calcul d'une cible au sol sur toute la largeur visible
                        const vFOV = THREE.MathUtils.degToRad(camera.fov);
                        const dist = camera.position.z;
                        const h = 2 * Math.tan(vFOV / 2) * dist;
                        const w = h * camera.aspect;
                        
                        l.targetPos.set(
                            (Math.random()-0.5) * w,  // X aléatoire sur la largeur
                            -5.0,                     // Y (Sol en bas)
                            (Math.random()-0.5) * 5   // Z Profondeur
                        );
                    }
                }

                // Fade In / Out
                const targetOp = l.isActive ? 0.6 : 0.0;
                l.beam.material.opacity += (targetOp - l.beam.material.opacity) * 0.1;
                l.dot.material.opacity = l.beam.material.opacity;

                // Mouvement du point d'impact
                l.currentPos.lerp(l.targetPos, l.speed);
                l.dot.position.copy(l.currentPos);

                // Orientation du laser : De la Source (Haut) vers le Point (Bas)
                l.beam.position.copy(sourceGroup.position);
                l.beam.lookAt(l.currentPos);
                
                // Étirement du laser pour toucher le sol
                const dist = sourceGroup.position.distanceTo(l.currentPos);
                l.beam.scale.z = dist;
            });
        }

        renderer.render(scene, camera);
    }

    // Gestion redimensionnement fenêtre
    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); 
        camera.aspect = width / height; 
        camera.updateProjectionMatrix();
        updateLayout(); // Recalcul de la position du titre
    });

    animate();
}
