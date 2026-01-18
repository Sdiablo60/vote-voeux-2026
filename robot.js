import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 - VOLANT & CYCLIQUE
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 6000; 
const VITESSE_VOL = 0.02; // Plus fluide
const ECHELLE_BOT = 0.65; 

// LIMITES ECRAN (Pour qu'il reste visible une fois entré)
const X_MAX_SCREEN = 13.0; 
const X_SAFE_CENTER = 6.0; // Ne pas aller entre -6 et 6

// BANQUES DE TEXTES (Tes textes d'origine conservés)
const TEXTS_ATTENTE = [
    "Clap-E scanne la salle... Vous êtes magnifiques !", "Je vole, donc je suis.", "Mon processeur chauffe, quelle ambiance !",
    "N'oubliez pas de voter tout à l'heure !", "J'ai un œil sur vous... et l'autre sur la régie.",
    "Bip Bop... Mise à jour du bonheur : 100%.", "Vous aimez mes nouveaux propulseurs ?",
    "La soirée va être mémorable !", "Je capte de bonnes ondes ici."
];
const TEXTS_VOTE_OFF = ["Les jeux sont faits !", "Calcul des résultats en cours...", "Chut... Je concentre mes circuits.", "Suspens..."];
const TEXTS_PHOTOS = ["Souriez ! Vous êtes filmés !", "Envoyez vos photos, je veux voir ça !", "Quelle belle grimace !", "Selfie time !"];

let currentTextBank = config.mode === 'vote_off' ? TEXTS_VOTE_OFF : (config.mode === 'photos' ? TEXTS_PHOTOS : TEXTS_ATTENTE);

// --- CSS BULLES ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base { position: fixed; padding: 15px 20px; color: black; font-family: 'Arial', sans-serif; font-weight: bold; font-size: 20px; text-align: center; z-index: 6; pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.9); max-width: 300px; width: max-content; }
    .bubble-speech { background: white; border-radius: 20px; border: 3px solid #E2001A; box-shadow: 0 0 15px rgba(226, 0, 26, 0.5); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%); border-left: 8px solid transparent; border-right: 8px solid transparent; border-top: 10px solid #E2001A; }
`;
document.head.appendChild(style);

function launchFinalScene() {
    ['robot-container', 'robot-canvas-floor', 'robot-canvas-bot', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    
    // Canvas Robot (Z-Index 5)
    const canvasBot = document.createElement('canvas'); canvasBot.id = 'robot-canvas-bot';
    document.body.appendChild(canvasBot);
    canvasBot.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 5; pointer-events: none; background: transparent;`;

    const bubbleEl = document.createElement('div'); bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);
    
    initThreeJS(canvasBot, bubbleEl);
}

function initThreeJS(canvasBot, bubbleEl) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100); 
    camera.position.set(0, 0, 14);

    const renderer = new THREE.WebGLRenderer({ canvas: canvasBot, antialias: true, alpha: true });
    renderer.setSize(width, height); renderer.setPixelRatio(window.devicePixelRatio);

    window.addEventListener('resize', () => { 
        const w = window.innerWidth, h = window.innerHeight;
        camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h);
    });

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xE2001A, 2); dirLight.position.set(5, 5, 5); scene.add(dirLight);

    // --- PARTICULES (EXPLOSION) ---
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(150 * 3);
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.3, transparent: true, opacity: 0 });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    // --- ROBOT (CONSTRUCTION) ---
    const robot = new THREE.Group(); robot.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    // Matériaux
    const matWhite = new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.2, metalness: 0.5 });
    const matBlack = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.1 });
    const matNeon = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const matRed = new THREE.MeshBasicMaterial({ color: 0xE2001A });

    // Corps & Tête
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), matWhite); body.position.y = -0.8;
    const head = new THREE.Group();
    const skull = new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 32), matWhite);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), matBlack); face.position.z = 0.25; face.scale.set(1, 0.8, 0.5);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.03, 8, 16), matNeon); eyeL.position.set(-0.3, 0.1, 0.85);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.3;
    
    // Propulseurs (Pieds)
    const propL = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.05, 0.5), matBlack); propL.position.set(-0.4, -1.6, 0);
    const propR = propL.clone(); propR.position.x = 0.4;
    const flame = new THREE.Mesh(new THREE.ConeGeometry(0.1, 0.4, 8), matRed); flame.position.y = -0.3; flame.rotation.x = Math.PI;
    propL.add(flame.clone()); propR.add(flame.clone());

    head.add(skull, face, eyeL, eyeR);
    robot.add(body, head, propL, propR);
    scene.add(robot);

    // --- LOGIQUE D'ANIMATION ---
    let time = 0;
    let state = 'entry'; // entry, idle, moving, bug, exit
    let targetPos = new THREE.Vector3(0, 0, 0);
    let bubbleTimer = 0;

    // Initialisation Entrée
    robot.position.set(-25, 5, -5); // Départ HORS CHAMP GAUCHE
    targetPos.set(0, 0, 0);

    function pickRandomOnScreenTarget() {
        // Choisir un coté (Gauche ou Droite) pour éviter le centre texte
        const side = Math.random() > 0.5 ? 1 : -1;
        // X entre 6 et 13 (Safe Zone)
        const x = side * (X_SAFE_CENTER + Math.random() * (X_MAX_SCREEN - X_SAFE_CENTER));
        const y = (Math.random() - 0.5) * 6; // Hauteur variée
        const z = (Math.random() * 4) - 2;   // Profondeur légère
        return new THREE.Vector3(x, y, z);
    }

    function showBubble(txt) {
        if(!txt) return;
        bubbleEl.innerHTML = txt;
        bubbleEl.className = 'robot-bubble-base bubble-speech';
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, 4000);
    }

    function triggerExplosion() {
        pMat.opacity = 1; particles.position.copy(robot.position);
        for(let i=0; i<150; i++) {
            pPos[i*3] = (Math.random()-0.5)*3; pPos[i*3+1] = (Math.random()-0.5)*3; pPos[i*3+2] = (Math.random()-0.5)*3;
        }
        pGeo.attributes.position.needsUpdate = true;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // 1. MOUVEMENT FLOTTANT (VOL)
        // On ajoute une oscillation sinusoïdale sur Y pour simuler le vol stationnaire
        const hoverY = Math.sin(time * 3) * 0.3;
        const currentPos = robot.position.clone();

        // 2. GESTION DES ETATS
        if (state === 'entry') {
            // Arrive vite vers le centre
            robot.position.lerp(new THREE.Vector3(0, 0, 0), 0.03);
            if (robot.position.distanceTo(new THREE.Vector3(0,0,0)) < 2) {
                state = 'idle'; showBubble("Bonjour les humains ! 👋");
            }
        } 
        else if (state === 'idle' || state === 'moving') {
            // Vol vers la cible
            const moveSpeed = VITESSE_VOL;
            robot.position.x += (targetPos.x - robot.position.x) * moveSpeed;
            robot.position.y += ((targetPos.y + hoverY) - robot.position.y) * moveSpeed;
            robot.position.z += (targetPos.z - robot.position.z) * moveSpeed;

            // Rotation douce vers la direction + regard vers camera
            robot.lookAt(camera.position); 

            // Changement de décision
            if (robot.position.distanceTo(targetPos) < 2 || Math.random() < 0.005) {
                targetPos = pickRandomOnScreenTarget();
                state = 'moving';
            }

            // Random Events
            if (Math.random() < 0.002) { // 0.2% chance par frame -> Bug
                state = 'bug';
                showBubble("ERREUR SYSTEME ! 🔥");
                triggerExplosion();
                setTimeout(() => { 
                    // Téléportation ailleurs
                    robot.position.copy(pickRandomOnScreenTarget());
                    state = 'idle'; 
                }, 1000);
            }
            
            // Parler
            if (time > bubbleTimer) {
                showBubble(currentTextBank[Math.floor(Math.random() * currentTextBank.length)]);
                bubbleTimer = time + 15 + Math.random() * 10;
            }
        }
        else if (state === 'bug') {
            // Tremblement
            robot.position.x += (Math.random()-0.5) * 0.5;
            robot.position.y += (Math.random()-0.5) * 0.5;
            robot.rotation.z += 0.5;
            // Particules qui s'écartent
            if(pMat.opacity > 0) {
                pMat.opacity -= 0.02;
                for(let i=0; i<150; i++) { pPos[i*3]*=1.05; pPos[i*3+1]*=1.05; pPos[i*3+2]*=1.05; }
                pGeo.attributes.position.needsUpdate = true;
            }
        }

        // Mise à jour position Bulle
        if (bubbleEl.style.opacity > 0) {
            const headPos = robot.position.clone(); headPos.y += 1.5; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * window.innerWidth;
            const y = (headPos.y * -.5 + .5) * window.innerHeight;
            bubbleEl.style.left = (x - bubbleEl.offsetWidth / 2) + 'px';
            bubbleEl.style.top = (y - bubbleEl.offsetHeight - 20) + 'px';
        }

        renderer.render(scene, camera);
    }
    
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', animate);
    else animate();
}
if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', launchFinalScene); } else { launchFinalScene(); }
