import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Grand Événement' };

// --- DIALOGUES ---
const DIALOGUES = {
    intro: [
        { text: "Bonjour à tous !", action: "agree", time: 3000 },
        { text: "Je suis votre I.A. de soirée.", action: "headShake", time: 3000 },
        { text: "Je vérifie les systèmes...", action: "idle", time: 2000 },
        { text: "Tout est opérationnel pour...", action: "agree", time: 2000 },
        { text: config.titre + " !", action: "headShake", time: 4000 },
        { text: "Y'a quelqu'un dans cet écran ?", action: "walk", time: 3000 }, // Clin d'oeil à votre image
        { text: "Bonne soirée !", action: "idle", time: 3000 }
    ],
    attente_loop: [
        "J'adore l'ambiance.", "N'oubliez pas de voter !", "Je surveille...", 
        "Quelle belle salle !", "Je suis prêt.", "Bip boup.", "Y'a quelqu'un ?"
    ],
    vote_off: [
        "Les votes sont CLÔTURÉS !", "Les jeux sont faits.", "Le podium arrive...",
        "Mais que fait la régie ?", "Calcul en cours...", "Suspens..."
    ],
    photos: [
        "C'est l'heure des photos !", "Souriez !", "Je veux être sur la photo !",
        "Allez, une petite grimace ?", "On partage !"
    ]
};

// --- SCÈNE & LUMIÈRE (POUR LE MÉTAL) ---
const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 1.6, 4.5); // Position pour bien voir le robot

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping; // Rend le métal réaliste
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

// CRUCIAL : Environnement pour que le métal brille (au lieu d'être rose/noir)
const pmremGenerator = new THREE.PMREMGenerator(renderer);
scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

// --- CHARGEMENT DU ROBOT ARGENTÉ (XBOT) ---
const MODEL_URL = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/models/gltf/Xbot.glb';

let mixer, activeAction, animations = {};

const loader = new GLTFLoader();
loader.load(MODEL_URL, function (gltf) {
    const model = gltf.scene;
    scene.add(model);
    
    model.position.y = -2.2; 
    model.scale.set(1.7, 1.7, 1.7); 

    // Ombres
    model.traverse(child => { if (child.isMesh) child.castShadow = true; });

    mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => { animations[clip.name] = mixer.clipAction(clip); });

    startBehaviorLogics();
    animate();
}, undefined, console.error);

// --- ANIMATIONS ---
function playAnim(name, duration = 0.5) {
    let target = 'idle';
    // Mapping des noms logiques vers les animations réelles du Xbot
    if (['Wave','agree'].includes(name)) target = 'agree';
    else if (['Talk','headShake'].includes(name)) target = 'headShake';
    else if (['run','Dance'].includes(name)) target = 'run';
    else if (['walk','Look'].includes(name)) target = 'walk';
    
    const newAction = animations[target];
    if (newAction && newAction !== activeAction) {
        if (activeAction) activeAction.fadeOut(duration);
        newAction.reset().fadeIn(duration).play();
        activeAction = newAction;
    }
}

function showBubble(text, duration = 3000) {
    bubble.innerHTML = text;
    bubble.style.opacity = 1;
    bubble.style.transform = "translate(-50%, -120px) scale(1)"; 
    setTimeout(() => {
        bubble.style.opacity = 0;
        bubble.style.transform = "translate(-50%, -100px) scale(0.8)";
    }, duration);
}

// --- LOGIQUE SCÉNARIO ---
async function startBehaviorLogics() {
    if (config.mode === 'attente') {
        for (let step of DIALOGUES.intro) {
            playAnim(step.action);
            showBubble(step.text, step.time - 500);
            await new Promise(r => setTimeout(r, step.time));
        }
        startRandomLoop('attente_loop');
    } else if (config.mode === 'vote_off') {
        playAnim('idle'); startRandomLoop('vote_off');
    } else if (config.mode === 'photos') {
        playAnim('run'); startRandomLoop('photos'); // Il court pendant les photos
    } else {
        startRandomLoop('attente_loop');
    }
}

function startRandomLoop(key) {
    setInterval(() => {
        if (Math.random() > 0.3) {
            const text = DIALOGUES[key][Math.floor(Math.random() * DIALOGUES[key].length)];
            const actions = ['headShake', 'agree', 'walk'];
            if(config.mode !== 'photos') playAnim(actions[Math.floor(Math.random() * actions.length)]);
            showBubble(text, 4000);
            setTimeout(() => { if(config.mode !== 'photos') playAnim('idle'); }, 3000);
        }
    }, 6000);
}

const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);
    if (mixer) mixer.update(clock.getDelta());
    renderer.render(scene, camera);
}
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
