import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT - MOUVEMENT FLUIDE & LINÉAIRE
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const VITESSE_LINEAIRE = 0.04; // Vitesse constante (plus d'impulsion)
const ECHELLE_BOT = 0.75; 

// LIMITES ECRAN (Zones latérales)
const X_MAX_SCREEN = 13.0; 
const X_SAFE_MIN = 7.0; // Reste à l'écart du centre (texte)

// BANQUES DE TEXTES
const TEXTS_ATTENTE = [
    "Clap-E est prêt !", "Je scanne la salle... Tout est OK.", 
    "N'oubliez pas de voter !", "Quelle belle ambiance ce soir.",
    "Bip Bop... Je suis votre serviteur.", "Préparez-vous !",
    "Je garde un œil sur vous."
];
const TEXTS_VOTE_OFF = ["Les votes sont clos.", "Calcul en cours...", "Patience...", "Le résultat arrive."];
const TEXTS_PHOTOS = ["Souriez !", "Envoyez vos photos !", "Photo time !", "Je veux voir vos sourires !"];

let currentTextBank = config.mode === 'vote_off' ? TEXTS_VOTE_OFF : (config.mode === 'photos' ? TEXTS_PHOTOS : TEXTS_ATTENTE);

// --- CSS BULLES ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base { position: fixed; padding: 15px 25px; color: black; font-family: 'Arial', sans-serif; font-weight: bold; font-size: 20px; text-align: center; z-index: 6; pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.9); max-width: 300px; width: max-content; }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -12px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
`;
document.head.appendChild(style);

function launchFinalScene() {
    ['robot-container', 'robot-canvas-floor', 'robot-canvas-bot', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    
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

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); scene.add(ambientLight);
    const spotLight = new THREE.SpotLight(0xffffff, 1.5); spotLight.position.set(10, 20, 10); scene.add(spotLight);

    // ==========================================
    // 🤖 ROBOT ORIGINAL
    // ==========================================
    const robotGroup = new THREE.Group(); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.2 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat); head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat); face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    
    // Corps & Bras
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    const armLGroup = new THREE.Group(); armLGroup.position.set(-0.9, -0.8, 0); 
    const armL = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armL.position.y = -0.2; 
    const handL = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handL.position.y = -0.5; 
    armLGroup.add(armL); armLGroup.add(handL);
    
    const armRGroup = new THREE.Group(); armRGroup.position.set(0.9, -0.8, 0);
    const armR = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armR.position.y = -0.2;
    const handR = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handR.position.y = -0.5;
    armRGroup.add(armR); armRGroup.add(handR);

    robotGroup.add(head, body, armLGroup, armRGroup);
    scene.add(robotGroup);

    // --- LOGIQUE DEPLACEMENT LISSE ---
    let time = 0;
    let targetPos = new THREE.Vector3(0, 0, 0);
    let bubbleTimer = 0;
    let isWaving = false;
    
    // Initialisation : Hors champ gauche
    robotGroup.position.set(-20, 0, 0);

    function pickTarget() {
        // Choisir un côté (Gauche ou Droite) pour éviter le texte central
        const side = Math.random() > 0.5 ? 1 : -1;
        // Position aléatoire dans la zone latérale
        const x = side * (X_SAFE_MIN + Math.random() * (X_MAX_SCREEN - X_SAFE_MIN));
        const y = (Math.random() - 0.5) * 4; // Hauteur variée
        return new THREE.Vector3(x, y, 0);
    }
    
    // Premier mouvement vers le centre (mais décalé)
    targetPos = new THREE.Vector3(-6, 0, 0);

    function showBubble(txt) {
        if(!txt) return;
        bubbleEl.innerHTML = txt;
        bubbleEl.className = 'robot-bubble-base bubble-speech';
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, 4000);
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // 1. CALCUL DU VECTEUR DE DIRECTION
        // On n'utilise plus lerp (qui ralentit à la fin). On avance à vitesse constante.
        const direction = new THREE.Vector3().subVectors(targetPos, robotGroup.position);
        const distance = direction.length();

        if (distance > 0.2) {
            // Si on est loin, on avance
            direction.normalize(); // Vecteur unitaire
            robotGroup.position.add(direction.multiplyScalar(VITESSE_LINEAIRE));
            
            // Rotation douce vers la cible (pour qu'il regarde où il va un peu)
            // Mais on garde le visage principalement vers la caméra
            const lookTarget = targetPos.clone();
            lookTarget.z = 10; // Force à regarder vers l'avant
            robotGroup.lookAt(lookTarget);
            
        } else {
            // Arrivé ! On choisit une nouvelle cible après une mini pause
            if(Math.random() < 0.05) targetPos = pickTarget();
        }

        // 2. OSCILLATION (Effet Flottant indépendant du mouvement)
        robotGroup.position.y += Math.sin(time * 2) * 0.008;

        // 3. BRAS (Animation)
        if (Math.random() < 0.005) isWaving = true;
        if (isWaving) {
            armRGroup.rotation.z = Math.sin(time * 15) * 0.5;
            armRGroup.rotation.x = -0.5;
            if (Math.random() < 0.02) { isWaving = false; armRGroup.rotation.set(0,0,0); }
        } else {
            armLGroup.rotation.z = Math.sin(time * 2) * 0.1;
            armRGroup.rotation.z = -Math.sin(time * 2) * 0.1;
        }

        // 4. PAROLE
        if (time > bubbleTimer) {
            showBubble(currentTextBank[Math.floor(Math.random() * currentTextBank.length)]);
            bubbleTimer = time + 10 + Math.random() * 10;
        }

        // 5. POSITION BULLE
        if (bubbleEl.style.opacity > 0) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.8; headPos.project(camera);
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
