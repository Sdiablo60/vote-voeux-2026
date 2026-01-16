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
        { text: "Bonne soirée !", action: "idle", time: 3000 }
    ],
    attente_loop: [
        "J'adore l'ambiance.", "N'oubliez pas de voter !", "Je surveille...", 
        "Quelle belle salle !", "Je suis prêt.", "Bip boup."
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

// --- SCÈNE & LUMIÈRE (C'EST ICI QUE LA MAGIE OPÈRE) ---
const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 1.6, 4.5); // Position idéale

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping; // Rend le métal plus réaliste
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

// AJOUT DE L'ENVIRONNEMENT (Pour que le métal brille)
const pmremGenerator = new THREE.PMREMGenerator(renderer);
scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

// --- CHARGEMENT DU ROBOT ARGENTÉ (XBOT) ---
const MODEL_URL = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/models/gltf/Xbot.glb';

let mixer, activeAction, animations = {};

const loader = new GLTFLoader();
loader.load(MODEL_URL, function (gltf) {
    const model = gltf.scene;
    scene.add(model);
    
    model.position.y = -2.2; // Hauteur ajustée
    model.scale.set(1.7, 1.7, 1.7); // Taille ajustée

    // Ombres portées (Optionnel pour le réalisme)
    model.traverse(child => { if (child.isMesh) child.castShadow = true; });

    mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => { animations[clip.name] = mixer.clipAction(clip); });

    startBehaviorLogics();
    animate();
}, undefined, console.error);

// --- ANIMATIONS & LOGIQUE ---
function playAnim(name, duration = 0.5) {
    let target = 'idle';
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
    bubble.style.transform = "translate(-50%, -120px) scale(1)"; // Bulle plus haute
    setTimeout(() => {
        bubble.style.opacity = 0;
        bubble.style.transform = "translate(-5
