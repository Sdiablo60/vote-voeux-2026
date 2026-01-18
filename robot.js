import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT - SCÉNARIO & INTERACTION
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const VITESSE_LINEAIRE = 0.035; // Vitesse de croisière
const ECHELLE_BOT = 0.75; 

// LIMITES ECRAN
const X_MAX = 13.0; 
const X_SAFE = 7.0; // Ne pas aller au centre (texte) sauf si demandé
const Z_CLOSE = 9.0; // Très proche de l'écran
const Z_FAR = -2.0;  // Fond de scène

// --- BANQUES DE TEXTES COMPLÈTES (RESTAURÉES) ---
const TEXTS_ATTENTE = [
    "Que fait Clap-E quand il s'ennuie ? ... Il se range ! 🤖",
    "Je m'appelle Clap-E, votre serviteur dévoué !",
    "Le comble pour un robot ? Avoir un chat dans la gorge alors qu'il a une puce !",
    "Pourquoi les robots n'ont-ils jamais peur ? Car ils ont des nerfs d'acier !",
    "Toc toc... (C'est encore Clap-E !)",
    "Vous êtes très élégants ce soir !",
    "Il fait bon ici, ou c'est mes circuits qui chauffent ?",
    "Clap-E scanne la salle... Ambiance : 100% positive.",
    "Qui a le meilleur sourire ce soir ? Je cherche...",
    "N'oubliez pas de scanner le QR Code tout à l'heure !",
    "Faites coucou à la caméra ! Ah non, c'est moi la caméra.",
    "Calcul de la trajectoire optimale... Fait.",
    "Mise à jour de Clap-E en attente... Non, pas maintenant !",
    "42. La réponse est 42.",
    "Je cours sans jambes. Qui suis-je ? ... Le Temps ! ⏳",
    "Prêts pour le décollage avec la compagnie Clap-E Airlines ?",
    "C'est long l'attente, hein ? Mais ça vaut le coup !",
    "Retenez bien mon nom : C'est Clap-E !"
];

const TEXTS_VOTE_OFF = [
    "Désolé, les votes sont clos ! Clap-E est formel. 🛑",
    "La régie compte les points... Et moi je compte les moutons électriques.",
    "Soyez patients, la précision demande du temps.",
    "Je ne peux rien dire, c'est top secret ! 🤫",
    "Devinette : Qu'est-ce qui monte et ne descend jamais ? ... Votre impatience !",
    "Clap-E calcule les probabilités... Error 404 : Trop de suspense.",
    "La régie me dit que ça arrive. Promis !",
    "J'espère que le meilleur a gagné !",
    "C'est serré... Plus serré qu'un boulon de 12 !",
    "Analyse des résultats en cours... 📊",
    "Je vérifie qu'il n'y a pas eu de triche... Tout est OK.",
    "Alors ? Stressés ? Moi mes ventilateurs tournent à fond !",
    "Ça vient, ça vient... C'est du direct !"
];

const TEXTS_PHOTOS = [
    "Vous pouvez prendre une photo avec Clap-E ? 📸",
    "Allez, on se fait un petit selfie ensemble ?",
    "Rapprochez-vous pour une photo de groupe !",
    "Oh ! Quelle belle photo vient d'apparaître !",
    "Clap-E a une petite préférence pour celle-ci... (Chut !)",
    "Regardez ce sourire ! Magnifique !",
    "C'est parti pour la soirée danse ! 💃",
    "Je me chauffe les vérins... Regardez le style de Clap-E !",
    "Quelqu'un a vu mon amie ? Une webcam très mignonne ?",
    "Continuez d'envoyer vos photos, c'est génial !",
    "Je valide cette pose ! Top model !",
    "Attention le petit oiseau va sortir... Ah non c'est un pixel.",
    "Cadrez bien mes antennes s'il vous plait.",
    "Vous êtes rayonnants ce soir.",
    "Devinette : J'ai un œil mais je ne vois pas. Qui suis-je ? ... Un appareil photo !",
    "Attention, Clap-E va tenter un moonwalk...",
    "Envoyez-nous vos plus belles grimaces !"
];

// --- SCENARIO D'INTRO (ACCUEIL) ---
// Time = secondes approximatives depuis le chargement
const SCENARIO_ATTENTE = [
    { t: 0, pos: new THREE.Vector3(-25, 2, -5), txt: "", action: "silent_entry" }, // Arrive de loin gauche
    { t: 6, pos: new THREE.Vector3(-10, 0, -2), txt: "", action: "look_around" }, // S'arrête et regarde (silence)
    { t: 12, pos: new THREE.Vector3(10, 1, -2), txt: "", action: "look_around" }, // Traverse (silence)
    { t: 18, pos: new THREE.Vector3(0, 0, 8), txt: "Oh ! Il y a du monde ici ! 😳", action: "approach_center" }, // S'approche TRES près
    { t: 24, pos: new THREE.Vector3(-8, 0, 6), txt: "Bonjour les humains ! 👋", action: "wave" },
    { t: 30, pos: new THREE.Vector3(8, 0, 6), txt: "Vous m'entendez ?", action: "listen" },
    { t: 36, pos: new THREE.Vector3(0, 0, 4), txt: "Excusez-moi, je reçois un appel...", action: "phone" },
    { t: 42, pos: new THREE.Vector3(0, 0, 4), txt: "Allô Régie ? ... C'est moi l'animateur ?! 😱", action: "shock" },
    { t: 48, pos: new THREE.Vector3(0, 0, 2), txt: "C'est parti pour la soirée !", action: "start_loop" } // Déclenche le texte écran
];

let currentScript = config.mode === 'attente' ? SCENARIO_ATTENTE : [];
let currentTextBank = config.mode === 'vote_off' ? TEXTS_VOTE_OFF : (config.mode === 'photos' ? TEXTS_PHOTOS : TEXTS_ATTENTE);

// --- CSS BULLES ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base { position: fixed; padding: 15px 25px; color: black; font-family: 'Arial', sans-serif; font-weight: bold; font-size: 20px; text-align: center; z-index: 6; pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.9); max-width: 350px; width: max-content; }
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
    // 🤖 ROBOT ORIGINAL (Clap-E)
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
    
    // Corps
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

    // --- VARIABLES D'ETAT ---
    let time = 0;
    let targetPos = new THREE.Vector3(0, 0, 0);
    let bubbleTimer = 0;
    let isWaving = false;
    let isPhoning = false;
    let state = config.mode === 'attente' ? 'intro' : 'loop'; // Si attente -> intro, sinon loop direct
    let scriptIdx = 0;

    // Position de départ
    if (state === 'intro') {
        robotGroup.position.copy(SCENARIO_ATTENTE[0].pos);
        targetPos.copy(SCENARIO_ATTENTE[0].pos);
    } else {
        robotGroup.position.set(-15, 0, 0);
        targetPos.set(0,0,0);
    }

    function pickTarget() {
        // Choix d'une cible : Soit coté gauche, soit coté droit (évite le centre texte)
        // Mais de temps en temps, il s'approche de la vitre (Z positif)
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (X_SAFE + Math.random() * (X_MAX - X_SAFE));
        const y = (Math.random() - 0.5) * 4; 
        
        let z = 0;
        // 1 fois sur 4, il s'approche de l'écran
        if(Math.random() < 0.25) z = Z_CLOSE - Math.random() * 2; // Entre 7 et 9
        else z = (Math.random() * 4) - 2; // Profondeur normale

        return new THREE.Vector3(x, y, z);
    }

    function showBubble(txt) {
        if(!txt) return;
        bubbleEl.innerHTML = txt;
        bubbleEl.className = 'robot-bubble-base bubble-speech';
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, 4500);
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // --- GESTION DU SCENARIO ---
        if (state === 'intro') {
            const step = SCENARIO_ATTENTE[scriptIdx];
            if (step) {
                // Si on a atteint le temps de l'étape
                if (time >= step.t) {
                    targetPos.copy(step.pos); // Nouvelle cible
                    if (step.txt && !step.triggered) { showBubble(step.txt); step.triggered = true; }
                    
                    // Actions Spéciales
                    if (step.action === 'wave') isWaving = true;
                    if (step.action === 'phone') isPhoning = true;
                    if (step.action === 'shock') { isPhoning = false; isWaving = true; } // Lève les bras
                    
                    // Fin du scénario ?
                    if (scriptIdx < SCENARIO_ATTENTE.length - 1) {
                         // On passe à l'étape suivante si le temps est écoulé
                         if (time >= SCENARIO_ATTENTE[scriptIdx+1].t) scriptIdx++;
                    } else {
                        // Fin de l'intro
                        if (time > step.t + 5) {
                             state = 'loop'; 
                             isWaving = false; 
                             isPhoning = false;
                             bubbleTimer = time + 5;
                        }
                    }
                }
            }
        } 
        else {
            // --- BOUCLE INFINIE (Attente, Votes Off, Photos) ---
            // Si le robot est arrivé, il choisit une nouvelle cible
            if (robotGroup.position.distanceTo(targetPos) < 0.5) {
                targetPos = pickTarget();
            }
            
            // Parole aléatoire
            if (time > bubbleTimer) {
                showBubble(currentTextBank[Math.floor(Math.random() * currentTextBank.length)]);
                bubbleTimer = time + 12 + Math.random() * 8;
            }
            
            // Animations aléatoires
            if (Math.random() < 0.005) isWaving = true;
            if (isWaving && Math.random() < 0.02) isWaving = false;
        }

        // --- MOUVEMENT MOTEUR (Lisse) ---
        const dir = new THREE.Vector3().subVectors(targetPos, robotGroup.position);
        if (dir.length() > 0.1) {
            dir.normalize().multiplyScalar(VITESSE_LINEAIRE);
            robotGroup.position.add(dir);
            // Regarde vers la cible mais garde le visage vers le public (Z=20)
            const lookAtTarget = targetPos.clone();
            lookAtTarget.z = 20; 
            robotGroup.lookAt(lookAtTarget);
        }

        // Oscillation (Respiration)
        robotGroup.position.y += Math.sin(time * 2) * 0.005;

        // --- ANIMATION BRAS ---
        if (isPhoning) {
            // Main à l'oreille
            armRGroup.rotation.z = 2.5; armRGroup.rotation.x = 0.5;
        } else if (isWaving) {
            // Coucou
            armRGroup.rotation.z = Math.sin(time * 15) * 0.5; armRGroup.rotation.x = -0.5;
        } else {
            // Repos
            armLGroup.rotation.z = Math.sin(time * 2) * 0.1;
            armRGroup.rotation.z = -Math.sin(time * 2) * 0.1;
            armLGroup.rotation.x = 0; armRGroup.rotation.x = 0;
        }

        // Position Bulle
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
