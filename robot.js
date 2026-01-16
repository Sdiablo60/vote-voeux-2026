import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// --- CONFIGURATION REÇUE DE PYTHON ---
const config = window.robotConfig || { mode: 'attente', titre: 'Grand Événement' };

// --- DONNÉES DE DIALOGUE ---
const DIALOGUES = {
    // 1. ACCUEIL
    intro: [
        { text: "Bonjour tout le monde !", action: "agree", time: 3000 }, // 'agree' remplace 'Wave'
        { text: "Je suis votre I.A. de soirée.", action: "headShake", time: 3000 }, // 'headShake' remplace 'Talk'
        { text: "Je regarde qui est là...", action: "idle", time: 3000 },
        { text: "Wouah ! Il y a du beau monde !", action: "agree", time: 3000 },
        { text: "Je suis né juste pour...", action: "headShake", time: 2000 },
        { text: config.titre + " !", action: "agree", time: 4000 },
        { text: "Profitez bien de la soirée !", action: "idle", time: 3000 }
    ],
    // 2. BOUCLE ATTENTE
    attente_loop: [
        "J'adore l'ambiance ici.",
        "N'oubliez pas de voter tout à l'heure !",
        "Je surveille tout...",
        "Quelle belle salle !",
        "Vous êtes prêts pour " + config.titre + " ?",
        "Je suis un robot très sophistiqué.",
        "Bip boup... Je plaisante."
    ],
    // 3. VOTE OFF
    vote_off: [
        "Les votes sont CLÔTURÉS !",
        "Les jeux sont faits...",
        "Merci de patienter un peu.",
        "Le podium va bientôt être révélé !",
        "Mais que fait la régie ?",
        "Ils calculent à la main ou quoi ?",
        "Suspens insoutenable...",
        "Ça arrive, ça arrive..."
    ],
    // 4. PHOTOS LIVE
    photos: [
        "C'est le moment des photos !",
        "Ne m'oubliez pas !",
        "Je veux être sur la photo aussi !",
        "Allez, faites une grimace !",
        "Montrez vos plus beaux sourires.",
        "On partage, on partage !"
    ]
};

// --- INITIALISATION THREE.JS ---
const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 1.5, 5); // Caméra un peu plus reculée pour le grand robot

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// Lumières (Plus fortes pour le métal)
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 2.0);
scene.add(hemiLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
dirLight.position.set(5, 10, 7.5);
scene.add(dirLight);

// --- CHARGEMENT DU MODÈLE ARGENTÉ (XBOT) ---
const MODEL_URL = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/models/gltf/Xbot.glb';

let mixer;
let animations = {};
let activeAction;
let model;

const loader = new GLTFLoader();
loader.load(MODEL_URL, function (gltf) {
    model = gltf.scene;
    scene.add(model);
    
    // Position du XBOT
    model.position.y = -2.5; // Plus bas car il est grand
    model.scale.set(1.8, 1.8, 1.8); // Plus grand

    // Gestion Animations
    mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => {
        animations[clip.name] = mixer.clipAction(clip);
    });

    // Lancer le comportement
    startBehaviorLogics();
    animate();

}, undefined, function (error) {
    console.error(error);
});

// --- GESTION DES ANIMATIONS ---
function playAnim(name, duration = 0.5) {
    // Mapping des noms d'animations du script vers celles du Xbot
    let targetAnim = 'idle'; // Défaut
    
    if (name === 'Wave' || name === 'agree') targetAnim = 'agree';
    else if (name === 'Talk' || name === 'headShake') targetAnim = 'headShake';
    else if (name === 'Dance' || name === 'run') targetAnim = 'run'; // Il court pour danser
    else if (name === 'Look' || name === 'walk') targetAnim = 'walk';
    else targetAnim = 'idle';

    const newAction = animations[targetAnim];
    
    if (newAction && newAction !== activeAction) {
        if (activeAction) activeAction.fadeOut(duration);
        newAction.reset().fadeIn(duration).play();
        activeAction = newAction;
    }
}

// --- BULLE DE DIALOGUE ---
function showBubble(text, duration = 3000) {
    bubble.innerHTML = text;
    bubble.style.opacity = 1;
    // Bulle plus haute pour le robot argenté
    bubble.style.transform = "translate(-50%, -100px) scale(1)"; 
    
    setTimeout(() => {
        bubble.style.opacity = 0;
        bubble.style.transform = "translate(-50%, -80px) scale(0.8)";
    }, duration);
}

// --- CERVEAU DU ROBOT ---
async function startBehaviorLogics() {
    if (config.mode === 'attente') {
        const sequence = DIALOGUES.intro;
        for (let step of sequence) {
            playAnim(step.action); 
            showBubble(step.text, step.time - 500);
            await new Promise(r => setTimeout(r, step.time));
        }
        startRandomLoop('attente_loop');
    } else if (config.mode === 'vote_off') {
        playAnim('idle'); 
        startRandomLoop('vote_off');
    } else if (config.mode === 'photos') {
        playAnim('run'); // Mode actif pour les photos
        startRandomLoop('photos');
    } else {
        startRandomLoop('attente_loop');
    }
}

function startRandomLoop(categoryKey) {
    const phrases = DIALOGUES[categoryKey];
    setInterval(() => {
        if (Math.random() > 0.3) {
            const text = phrases[Math.floor(Math.random() * phrases.length)];
            const actions = ['headShake', 'agree', 'walk']; // Animations dispos du Xbot
            const rndAction = actions[Math.floor(Math.random() * actions.length)];
            
            if(config.mode === 'photos' && Math.random() > 0.5) {
                 // Reste en course
            } else {
                 playAnim(rndAction);
            }
            showBubble(text, 4000);
            
            setTimeout(() => {
                if(config.mode === 'photos') playAnim('run');
                else playAnim('idle');
            }, 3000);
        }
    }, 6000);
}

// --- BOUCLE DE RENDU ---
const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
