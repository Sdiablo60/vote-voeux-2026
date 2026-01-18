import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT 2026 (FINAL - PHOTOS INTERACTIF)
// =========================================================
const LIMITE_HAUTE_Y = 6.53; 
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 7500; 
const VITESSE_MOUVEMENT = 0.008; 
const ECHELLE_BOT = 0.6; 
const SPEED_THRESHOLD = 0.02; 

// ZONE INTERDITE ÉLARGIE (Le robot reste sur les cotés en mode libre)
const SAFE_ZONE_X = 9.0; 

const CENTRAL_MESSAGES = [
    "Votre soirée va bientôt commencer...<br>Merci de vous installer",
    "Une soirée exceptionnelle vous attend",
    "Veuillez couper la sonnerie<br>de vos téléphones 🔕",
    "Profitez de l'instant et du spectacle",
    "Préparez-vous à jouer !",
    "N'oubliez pas vos sourires !"
];

// --- BANQUES DE TEXTES ---

const TEXTS_ATTENTE = [
    "Que fait un robot quand il s'ennuie ? ... Il se range ! 🤖",
    "Le comble pour un robot ? Avoir un chat dans la gorge alors qu'il a une puce !",
    "Pourquoi les robots n'ont-ils jamais peur ? Car ils ont des nerfs d'acier !",
    "Toc toc... (C'est moi)",
    "Vous êtes très élégants ce soir !",
    "Il fait bon ici, ou c'est mes circuits qui chauffent ?",
    "Je scanne la salle... Ambiance : 100% positive.",
    "Qui a le meilleur sourire ce soir ? Je cherche...",
    "N'oubliez pas de scanner le QR Code tout à l'heure !",
    "Faites coucou à la caméra ! Ah non, c'est moi la caméra.",
    "Calcul de la trajectoire optimale... Fait.",
    "Mise à jour système en attente... Non, pas maintenant !",
    "42. La réponse est 42.",
    "Je cours sans jambes. Qui suis-je ? ... Le Temps ! ⏳",
    "Prêts pour le décollage ?",
    "C'est long l'attente, hein ? Mais ça vaut le coup !",
    "Je suis tellement content d'être votre animateur."
];

const TEXTS_VOTE_OFF = [
    "Désolé, les votes sont clos ! 🛑",
    "La régie compte les points... 1, 2, 3... beaucoup !",
    "Soyez patients, la précision demande du temps.",
    "Je ne peux rien dire, c'est top secret ! 🤫",
    "Devinette : Qu'est-ce qui monte et ne descend jamais ? ... Votre impatience !",
    "Je calcule les probabilités... Error 404 : Trop de suspense.",
    "La régie me dit que ça arrive. Promis !",
    "J'espère que le meilleur a gagné !",
    "C'est serré... Plus serré qu'un boulon de 12 !",
    "Analyse des résultats en cours... 📊",
    "Je vérifie qu'il n'y a pas eu de triche... Tout est OK.",
    "Alors ? Stressés ? Moi mes ventilateurs tournent à fond !",
    "Ça vient, ça vient... C'est du direct !",
    "Les résultats sont en cours de téléchargement...",
    "Merci à tous d'avoir participé, c'était intense."
];

// --- TEXTES SPÉCIFIQUES PHOTOS (Selfies, Groupes, Avis) ---
const TEXTS_PHOTOS = [
    "Vous pouvez me prendre en photo ? 📸",
    "Allez, on se fait un petit selfie ensemble ?",
    "Rapprochez-vous pour une photo de groupe !",
    "Oh ! Quelle belle photo vient d'apparaître !",
    "J'ai une petite préférence pour celle-ci... (Chut !)",
    "Regardez ce sourire ! Magnifique !",
    "C'est parti pour la soirée danse ! 💃",
    "Je me chauffe les vérins... Regardez ce style !",
    "Quelqu'un a vu mon amie ? Une webcam très mignonne ?",
    "Continuez d'envoyer vos photos, c'est génial !",
    "Je valide cette pose ! Top model !",
    "Attention le petit oiseau va sortir... Ah non c'est un pixel.",
    "Cadrez bien mes antennes s'il vous plait.",
    "Vous êtes rayonnants ce soir.",
    "Devinette : J'ai un œil mais je ne vois pas. Qui suis-je ? ... Un appareil photo !",
    "Attention, je vais tenter un moonwalk...",
    "Envoyez-nous vos plus belles grimaces !",
    "Flash info : Vous êtes le meilleur public !",
    "On veut plus de photos de groupe ! Serrez-vous !",
    "Mes capteurs de rythme sont au maximum."
];

let currentTextBank = [];
if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
else currentTextBank = [...TEXTS_ATTENTE];

// --- STYLE CSS ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base {
        position: fixed; padding: 20px 25px; color: black; font-family: 'Arial', sans-serif;
        font-weight: bold; font-size: 22px; text-align: center; z-index: 2147483647;
        pointer-events: none; transition: opacity 0.5s, transform 0.3s; transform: scale(0.9); 
        max-width: 350px; width: max-content;
    }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -15px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
    .bubble-thought { background: white; border-radius: 50%; border: 4px solid #00ffff; box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-style: italic; color: #555; }
    .bubble-thought::before { content: ''; position: absolute; bottom: -10px; left: 30%; width: 15px; height: 15px; background: white; border: 2px solid #00ffff; border-radius: 50%; }
`;
document.head.appendChild(style);

// --- SCENARIO 1 : ACCUEIL ---
const introScript_Attente = [
    { time: 4, text: "", action: "enter_scene_slow" }, 
    { time: 10, text: "Wouah... C'est grand ici !", type: "thought", action: "look_around" },
    { time: 18, text: "Je crois que je suis le premier arrivé...", type: "thought", action: "move_right_slow" },
    { time: 26, text: "Tiens ? C'est quoi cette lumière ?", type: "thought", action: "move_left_check" },
    { time: 34, text: "OH ! Mais... Il y a du monde en fait ! 😳", type: "speech", action: "surprise_stop" },
    { time: 42, text: "Bonjour tout le monde ! 👋", type: "speech", action: "move_center_wave" },
    { time: 50, text: "Vous êtes nombreux ce soir ! Bienvenue !", type: "speech" }, 
    { time: 58, text: "", action: "toc_toc_approach" }, 
    { time: 60, text: "Toc ! Toc ! Vous m'entendez là-dedans ?", type: "speech" }, 
    { time: 68, text: "Ah ! Vous êtes bien réels ! 😅", type: "speech", action: "backup_a_bit" },
    { time: 76, text: "Votre visage me dit quelque chose monsieur...", type: "thought", action: "scan_crowd" },
    { time: 84, text: "Hum, non, je dois confondre avec une star. 😎", type: "speech" },
    { time: 92, text: "Excusez-moi, je reçois un appel...", type: "speech", action: "phone_call" },
    { time: 100, text: "Allô la régie ? Oui c'est le Robot.", type: "speech" },
    { time: 108, text: "QUOI ?! C'est confirmé ?!", type: "speech", action: "surprise" },
    { time: 116, text: "Incroyable ! On vient de me nommer Animateur de la soirée ! 🎤", type: "speech", action: "start_subtitles" },
    { time: 124, text: "Bienvenue à : " + config.titre + " !", type: "speech" },
    { time: 132, text: "Ouhlà... Je n'ai pas préparé mes fiches...", type: "thought", action: "stress_pacing" },
    { time: 140, text: "Est-ce que ma batterie est assez chargée ? 🔋", type: "thought" },
    { time: 148, text: "Oui Régie ? Il manque un câble ?", type: "speech", action: "listen_intense" },
    { time: 156, text: "Mince ! Je dois filer en coulisses !", type: "speech" },
    { time: 164, text: "Je reviens tout de suite ! 🏃‍♂️", type: "speech", action: "exit_right_normal" }, 
    { time: 180, text: "Me revoilà ! 😅", type: "speech", action: "enter_left_fast" },
    { time: 188, text: "C'était moins une, on a failli perdre le wifi !", type: "speech", action: "center_breath" },
    { time: 196, text: "La régie me confirme : La soirée va bientôt commencer ! 🎉", type: "speech", action: "announce_pose" },
    { time: 204, text: "Installez-vous bien, je veille sur vous.", type: "speech" }
];

// --- SCENARIO 2 : VOTE OFF ---
const introScript_VoteOff = [
    { time: 2, text: "", action: "enter_teleport_left" }, 
    { time: 8, text: "Oula... C'est fini !", type: "speech" },
    { time: 15, text: "Désolé les amis, les votes sont clos ! 🛑", type: "speech", action: "move_right_slow" },
    { time: 22, text: "La régie est en train de compter les points...", type: "speech" },
    { time: 29, text: "Soyez patients, ça arrive !", type: "speech", action: "move_left_check" }, 
    { time: 36, text: "Je ne dis rien, mais c'était serré... 🤫", type: "speech" }
];

// --- SCENARIO 3 : PHOTOS LIVE (Interactif & Selfie) ---
const introScript_Photos = [
    { time: 2, text: "", action: "enter_teleport_right" }, // Arrive droite
    { time: 8, text: "Wouah ! C'est ici le studio photo ?", type: "speech", action: "move_center_wave" }, // Va au milieu
    { time: 15, text: "Vous pouvez me prendre en photo ? 📸", type: "speech", action: "toc_toc_approach" }, // Gros plan
    { time: 22, text: "Attention... 3, 2, 1... Cheese !", type: "speech", action: "pose_selfie" }, // Pose fixe
    { time: 29, text: "J'espère que je n'ai pas fermé les yeux...", type: "thought", action: "backup_a_bit" },
    { time: 36, text: "Hop ! Je me téléporte !", type: "speech", action: "enter_teleport_left" }, // TP Gauche
    { time: 42, text: "Oh regardez celle-ci ! Magnifique !", type: "speech", action: "look_bubbles" }, // Regarde en l'air
    { time: 49, text: "J'ai une petite préférence pour ce sourire là-haut...", type: "speech" },
    { time: 56, text: "Allez, soirée danse pour fêter ça !", type: "speech", action: "dance_start" }
];

let currentIntroScript = introScript_Attente;
if (config.mode === 'vote_off') currentIntroScript = introScript_VoteOff;
if (config.mode === 'photos') currentIntroScript = introScript_Photos;

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', launchFinalScene); } else { launchFinalScene(); }

function launchFinalScene() {
    ['robot-container', 'robot-canvas-overlay', 'robot-canvas-final', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    const canvas = document.createElement('canvas'); canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);
    canvas.style.cssText = `position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 1; pointer-events: none !important; background: transparent !important;`;
    const bubbleEl = document.createElement('div'); bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);
    initThreeJS(canvas, bubbleEl);
}

function initThreeJS(canvas, bubbleEl) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x000000, 10, 60);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height); renderer.setPixelRatio(window.devicePixelRatio);
    window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
    
    scene.add(new THREE.AmbientLight(0xffffff, 2.0));

    // SOL GRIS (SANS LIGNE ROUGE)
    const grid = new THREE.GridHelper(200, 50, 0x222222, 0x222222);
    grid.position.y = -2.5; 
    scene.add(grid);

    // PARTICULES (TELEPORTATION)
    const particleCount = 100;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.2, transparent: true, opacity: 0 });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);
    let explosionTime = 0;
    let isExploding = false;

    function triggerTeleport(pos) {
        isExploding = true;
        explosionTime = 1.0; 
        particles.position.copy(pos);
        particleMat.opacity = 1;
        for(let i=0; i<particleCount; i++) {
            particlePositions[i*3] = (Math.random()-0.5)*2;
            particlePositions[i*3+1] = (Math.random()-0.5)*4;
            particlePositions[i*3+2] = (Math.random()-0.5)*2;
        }
        particleGeo.attributes.position.needsUpdate = true;
    }

    // ROBOT
    const robotGroup = new THREE.Group(); 
    robotGroup.position.set(-35, 0, 0); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat); head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat); face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat); leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat); rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;
    [head, body, leftArm, rightArm].forEach(p => { robotGroup.add(p); p.userData.origPos = p.position.clone(); p.userData.origRot = p.rotation.clone(); p.userData.velocity = new THREE.Vector3(); });
    scene.add(robotGroup);

    const stageSpots = [];
    [-8, -3, 3, 8].forEach((x, i) => {
        const g = new THREE.Group(); g.position.set(x, LIMITE_HAUTE_Y, 0);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color: [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00][i%4], transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g); stageSpots.push({ g, beam, isOn: false, nextToggle: Math.random()*5 });
    });

    let robotState = 'intro';
    let time = 0, nextEvt = 0, nextMoveTime = 0, introIdx = 0;
    let targetPos = new THREE.Vector3(-35, 0, 0); 
    let lastPos = new THREE.Vector3();
    let lastTextChange = 0;
    let textMsgIndex = 0;
    let subtitlesActive = false; 

    function showBubble(text, type = 'speech') { 
        if(!text) return;
        bubbleEl.innerHTML = text; 
        bubbleEl.className = 'robot-bubble-base ' + (type === 'thought' ? 'bubble-thought' : 'bubble-speech');
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, DUREE_LECTURE); 
    }

    function cycleCenterText() {
        const subDiv = document.getElementById('sub-text');
        if(subDiv && subtitlesActive) {
            subDiv.style.opacity = 0;
            setTimeout(() => { subDiv.innerHTML = CENTRAL_MESSAGES[textMsgIndex % CENTRAL_MESSAGES.length]; subDiv.style.opacity = 1; textMsgIndex++; }, 1000); 
        }
    }

    function pickNewTarget() {
        const dist = camera.position.z; const vFOV = THREE.MathUtils.degToRad(camera.fov);
        const visibleHeight = 2 * Math.tan(vFOV / 2) * dist; const visibleWidth = visibleHeight * camera.aspect;
        const xLimit = (visibleWidth / 2) - 2.5; 
        const side = Math.random() > 0.5 ? 1 : -1;
        
        // ZONE INTERDITE : X > 9.0 ou X < -9.0
        const randomX = SAFE_ZONE_X + (Math.random() * (xLimit - SAFE_ZONE_X)); 
        
        targetPos.set(side * randomX, (Math.random() - 0.5) * 6, (Math.random() * 5) - 3);
        if(targetPos.y > LIMITE_HAUTE_Y - 2.5) targetPos.y = LIMITE_HAUTE_Y - 3;
        nextMoveTime = Date.now() + 8000; 
    }

    function getNextMessage() {
        if (currentTextBank.length === 0) {
            if (config.mode === 'vote_off') currentTextBank = [...TEXTS_VOTE_OFF];
            else if (config.mode === 'photos') currentTextBank = [...TEXTS_PHOTOS];
            else currentTextBank = [...TEXTS_ATTENTE];
        }
        const idx = Math.floor(Math.random() * currentTextBank.length);
        const msg = currentTextBank[idx];
        currentTextBank.splice(idx, 1);
        return msg;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;
        const currentSpeed = robotGroup.position.distanceTo(lastPos);

        // Animation particules
        if(isExploding && explosionTime > 0) {
            explosionTime -= 0.02;
            particleMat.opacity = explosionTime;
            const positions = particleGeo.attributes.position.array;
            for(let i=0; i<100; i++) {
                positions[i*3] += (Math.random()-0.5)*0.1; 
                positions[i*3+1] += (Math.random()-0.5)*0.1;
                positions[i*3+2] += (Math.random()-0.5)*0.1;
            }
            particleGeo.attributes.position.needsUpdate = true;
        }

        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.12 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        // --- GESTION SCENARIOS ---
        if (robotState === 'intro') {
            const step = currentIntroScript[introIdx];
            if (step && time >= step.time) {
                if (currentSpeed < SPEED_THRESHOLD || step.action?.includes("fast") || step.action?.includes("normal") || step.action?.includes("teleport")) {
                    if(step.text) showBubble(step.text, step.type);
                }
                
                // Mouvements standards
                if(step.action === "enter_scene_slow") targetPos.set(-7, 2, -2);
                
                // ZONES SAFE pour les murs chargés (Vote/Photos)
                if(step.action === "move_right_slow") targetPos.set(10, 1, -2); 
                if(step.action === "move_left_check") targetPos.set(-10, -1, 0); 
                
                if(step.action === "look_around") targetPos.set(0, 0, -5);
                if(step.action === "surprise_stop") targetPos.set(-6, 0, 4);
                if(step.action === "move_center_wave") targetPos.set(0, 0, 5);
                
                // Gros plan & Selfie
                if(step.action === "toc_toc_approach") targetPos.set(1.5, 0, 8.5); 
                if(step.action === "backup_a_bit") targetPos.set(1.5, 0, 5);
                if(step.action === "pose_selfie") { robotState = 'posing'; setTimeout(() => { robotState = 'intro'; }, 3000); }
                
                // Regarde les bulles
                if(step.action === "look_bubbles") { targetPos.set(0, 4, 0); }

                if(step.action === "scan_crowd") targetPos.set(-10, 1, 4);
                if(step.action === "phone_call") targetPos.set(10, 0, 2);
                if(step.action === "surprise") targetPos.set(10, 0, 6);
                if(step.action === "start_subtitles") { subtitlesActive = true; cycleCenterText(); lastTextChange = time; }
                if(step.action === "stress_pacing") targetPos.set(-10, -2, 0);
                if(step.action === "listen_intense") targetPos.set(0, 0, 5);
                if(step.action === "exit_right_normal") targetPos.set(35, 0, 0); 
                if(step.action === "exit_right_fast") targetPos.set(35, 0, 0); 
                
                if(step.action === "enter_left_fast") { robotGroup.position.set(-35, 0, 0); targetPos.set(-10, 0, 4); }
                if(step.action === "center_breath") targetPos.set(0, 0, 3);
                if(step.action === "announce_pose") targetPos.set(-5, 1, 6); 
                
                // TELEPORTATIONS
                if(step.action === "enter_teleport_left") { 
                    robotGroup.position.set(-35, 0, 0); 
                    targetPos.set(-10, 0, 0); 
                    triggerTeleport(new THREE.Vector3(-10, 0, 0));
                }
                if(step.action === "enter_teleport_right") { 
                    robotGroup.position.set(35, 0, 0); 
                    targetPos.set(10, 0, 0); 
                    triggerTeleport(new THREE.Vector3(10, 0, 0));
                }

                // DANSE
                if(step.action === "dance_start") { 
                    robotState = 'dancing_intro'; 
                    setTimeout(() => { if(robotState === 'dancing_intro') robotState = 'intro'; }, 5000); 
                }
                if(step.action === "dance_stop") {
                    robotState = 'intro'; 
                    robotGroup.rotation.set(0, 0, 0); // RESET ROTATION
                }
                
                introIdx++;
            }
            
            if(introIdx >= currentIntroScript.length) { 
                robotState = 'infinite_loop'; pickNewTarget(); nextEvt = time + 10; 
            }
            
            // Pas de mouvement pendant la pose selfie ou la danse
            if(robotState !== 'dancing_intro' && robotState !== 'posing') {
                let speedFactor = VITESSE_MOUVEMENT;
                if (step && step.action === "exit_right_normal") speedFactor = 0.015; 
                else if(targetPos.x > 20 || targetPos.x < -20) speedFactor = 0.04; 
                else if(targetPos.z > 7) speedFactor = 0.02; 
                robotGroup.position.lerp(targetPos, speedFactor);
            }
        } 
        
        // --- BOUCLE INFINIE ---
        else if (robotState === 'infinite_loop' || robotState === 'approaching' || robotState === 'thinking') {
            if (config.mode === 'attente' && subtitlesActive && time > lastTextChange + 12) { cycleCenterText(); lastTextChange = time; }
            if (Date.now() > nextMoveTime || robotState === 'approaching') robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT);
            robotGroup.rotation.y = Math.sin(time)*0.2;
            
            if(robotGroup.position.distanceTo(targetPos) < 0.5 && robotState !== 'thinking') {
                if (robotState === 'approaching') { robotState = 'infinite_loop'; pickNewTarget(); }
                else if (Date.now() > nextMoveTime) pickNewTarget(); 
            }
            
            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.08) { 
                    robotState = 'exploding'; showBubble("Surchauffe ! 🔥"); 
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4)); 
                    setTimeout(() => { robotState = 'reassembling'; }, 3500); nextEvt = time + 25;
                }
                else if (config.mode === 'photos' && r < 0.25) {
                    robotState = 'dancing';
                    showBubble("C'est ma chanson préférée !", 'speech');
                    setTimeout(() => { 
                        robotState = 'infinite_loop'; 
                        robotGroup.rotation.set(0,0,0); 
                        pickNewTarget(); 
                    }, 6000); 
                    nextEvt = time + 20;
                }
                // NOUVEAU : TELEPORTATION ALEATOIRE EN MODE LIBRE (Si pas accueil)
                else if (config.mode !== 'attente' && r < 0.40) {
                    const side = Math.random() > 0.5 ? 10 : -10;
                    robotGroup.position.set(side * -1, 0, 0); // TP opposé
                    targetPos.set(side, 0, 0);
                    triggerTeleport(robotGroup.position);
                    nextEvt = time + 10;
                }
                else if (currentSpeed < SPEED_THRESHOLD) { 
                    const msg = getNextMessage(); 
                    const type = (msg.includes("Hmm") || msg.includes("Calcul") || msg.includes("Analyse")) ? 'thought' : 'speech';
                    showBubble(msg, type);
                    nextEvt = time + 15; 
                } else { nextEvt = time + 2; }
            }
        }
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.05; p.userData.velocity.multiplyScalar(0.98); }); }
        else if (robotState === 'reassembling') {
            let finished = true;
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.1; if (p.position.distanceTo(p.userData.origPos) > 0.05) finished = false; });
            if(finished) { 
                parts.forEach(p => { p.position.copy(p.userData.origPos); p.rotation.copy(p.userData.origRot); }); 
                robotState = 'infinite_loop'; nextEvt = time + 5; pickNewTarget(); nextMoveTime = 0; 
            }
        }
        else if (robotState === 'dancing' || robotState === 'dancing_intro') {
            robotGroup.rotation.y += 0.15; 
            robotGroup.position.y = Math.abs(Math.sin(time * 5)) * 0.5; 
        }
        else if (robotState === 'posing') {
            robotGroup.rotation.y = 0; // Face caméra
            robotGroup.rotation.z = Math.sin(time * 2) * 0.1; // Penche la tête mignon
        }

        if(bubbleEl && bubbleEl.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.3 + (robotGroup.position.z * 0.05); headPos.project(camera);
            const bX = (headPos.x * 0.5 + 0.5) * window.innerWidth;
            const bY = (headPos.y * -0.5 + 0.5) * window.innerHeight;
            let leftPos = (bX - bubbleEl.offsetWidth / 2);
            leftPos = Math.max(20, Math.min(leftPos, window.innerWidth - bubbleEl.offsetWidth - 20)); 
            bubbleEl.style.left = leftPos + 'px';
            bubbleEl.style.top = (bY - bubbleEl.offsetHeight - 25) + 'px';
            if(parseFloat(bubbleEl.style.top) < 140) bubbleEl.style.top = '140px';
        }
        lastPos.copy(robotGroup.position);
        renderer.render(scene, camera);
    }
    animate();
}
