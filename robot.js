import * as THREE from 'three';

// =========================================================
// 🔴 CALIBRAGE AUTOMATIQUE (FINI LES RÉGLAGES MANUELS) 🔴
// =========================================================
// Votre bandeau rouge dans app.py fait exactement 12% de l'écran (12vh).
// On dit au robot de descendre exactement de ce pourcentage.
const HAUTEUR_TITRE_POURCENTAGE = 0.12; 

// On garde la largeur à 100%
const FACTEUR_LARGEUR = 1.0; 
// =========================================================

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchRobotScene);
} else {
    launchRobotScene();
}

function launchRobotScene() {
    const oldIds = ['robot-container', 'robot-canvas-overlay', 'robot-ghost-layer', 'robot-canvas-final', 'robot-calibration-layer'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
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

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- SYSTÈME LASERS ---
    // =========================================================
    const lasers = [];
    const sourceGroup = new THREE.Group();
    scene.add(sourceGroup);

    // Initialisation Lasers
    const colors = [0x00FF00, 0x00FFFF, 0x0055FF, 0xFF00FF, 0xFFFF00, 0xFF3300, 0xFFFFFF];
    // On génère les lasers mais ils sont invisibles au départ
    for(let i=0; i<12; i++) { 
        const color = colors[Math.floor(Math.random()*colors.length)];
        const beam = new THREE.Mesh(
            new THREE.CylinderGeometry(0.04, 0.04, 1, 8, 1, true),
            new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false })
        );
        beam.rotateX(Math.PI / 2);
        beam.geometry.translate(0, 0.5, 0);
        scene.add(beam);

        const dot = new THREE.Mesh(
            new THREE.CircleGeometry(0.5, 16),
            new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, side: THREE.DoubleSide })
        );
        dot.rotation.x = -Math.PI / 2;
        scene.add(dot);

        lasers.push({ beam: beam, dot: dot, targetPos: new THREE.Vector3(0, -4, 0), currentPos: new THREE.Vector3(0, -4, 0), speed: 0.02 + Math.random()*0.03, isActive: false });
    }

    // --- LE CADRE DE DEBUG (POUR VÉRIFIER) ---
    // Je laisse ce cadre rouge. S'il touche la barre blanche, c'est gagné.
    const borderGeo = new THREE.BufferGeometry();
    const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 3 });
    const borderLine = new THREE.LineLoop(borderGeo, borderMat);
    scene.add(borderLine);

    // FONCTION DE CALCUL PRÉCIS (MATHÉMATIQUE)
    const updateLayout = () => {
        const dist = camera.position.z; 
        const vFOV = THREE.MathUtils.degToRad(camera.fov);
        
        // Hauteur totale visible en unités 3D
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
        const visibleWidth = visibleHeight * camera.aspect;

        const halfH = visibleHeight / 2;
        const halfW = visibleWidth / 2;

        // CALCUL MAGIQUE : 12% de la hauteur totale = La hauteur du bandeau rouge
        const hauteurBandeau3D = visibleHeight * HAUTEUR_TITRE_POURCENTAGE;
        
        // Le point de départ (yTop) est le haut de l'écran MOINS la hauteur du bandeau
        // On rajoute un petit 0.1 de sécurité pour être sûr d'être sous la barre blanche
        const yTop = halfH - hauteurBandeau3D - 0.1;
        
        const yBottom = -halfH;
        const xRight = halfW * FACTEUR_LARGEUR;
        const xLeft = -xRight;

        // 1. Placement de la source des lasers
        sourceGroup.position.set(0, yTop, 0);

        // 2. Mise à jour du cadre rouge pour vérification
        const points = [
            new THREE.Vector3(xLeft, yTop, 0),
            new THREE.Vector3(xRight, yTop, 0),
            new THREE.Vector3(xRight, yBottom, 0),
            new THREE.Vector3(xLeft, yBottom, 0)
        ];
        borderGeo.setFromPoints(points);
    };
    updateLayout();
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
    let targetPosition = new THREE.Vector3(0, -1.5, 0); 
    robotGroup.position.copy(targetPosition);

    // ANIMATION
    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;
        robotGroup.position.y = -1.5 + Math.sin(time*2) * 0.1;

        // Lasers Logic
        const activeCount = lasers.filter(l => l.isActive).length;
        lasers.forEach(l => {
            if(Math.random() > 0.98) {
                if(l.isActive) l.isActive = false;
                else if(activeCount < 8) {
                    l.isActive = true;
                    // Cible au sol (-4.5) sur toute la largeur (visibleWidth)
                    const vFOV = THREE.MathUtils.degToRad(camera.fov);
                    const h = 2 * Math.tan(vFOV / 2) * 14;
                    const w = h * camera.aspect;
                    l.targetPos.set((Math.random()-0.5) * w, -4.5, (Math.random()-0.5) * 5);
                }
            }
            const targetOp = l.isActive ? 0.7 : 0.0;
            l.beam.material.opacity += (targetOp - l.beam.material.opacity) * 0.1;
            l.dot.material.opacity = l.beam.material.opacity;
            l.currentPos.lerp(l.targetPos, l.speed);
            l.dot.position.copy(l.currentPos);
            l.beam.position.copy(sourceGroup.position);
            l.beam.lookAt(l.currentPos);
            l.beam.scale.z = sourceGroup.position.distanceTo(l.currentPos);
        });

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); 
        camera.aspect = width / height; 
        camera.updateProjectionMatrix();
        updateLayout();
    });

    animate();
}
