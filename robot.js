import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// --- CONFIGURATION REÇUE DE PYTHON ---
// On récupère le titre et le mode, ou des valeurs par défaut
const config = window.robotConfig || { mode: 'attente', titre: 'Grand Événement' };
console.log("Robot Config:", config);

// --- DONNÉES DE DIALOGUE ---
const DIALOGUES = {
    // 1. ACCUEIL : Séquence d'intro
    intro: [
        { text: "Bonjour tout le monde !", action: "Wave", time: 3000 },
        { text: "Je suis votre I.A. de soirée.", action: "Talk", time: 3000 },
        { text: "Je regarde qui est là...", action: "Look", time: 3000 },
        { text: "Wouah ! Il y a du beau monde !", action: "Yes", time: 3000 },
        { text: "Je suis né juste pour...", action: "Talk", time: 2000 },
        { text: config.titre + " !", action: "Wave", time: 4000 }, // Affiche le titre dynamique
        { text: "Profitez bien de la soirée !", action: "Idle", time: 3000 }
    ],
    // 2. ACCUEIL (Boucle après l'intro)
    attente_loop: [
        "J'adore l'ambiance ici.",
        "N'oubliez pas de voter tout à l'heure !",
        "Je surveille tout...",
        "Quelle belle salle !",
        "Vous êtes prêts pour " + config.titre + " ?",
        "Je suis un robot très sophistiqué, vous savez.",
        "Bip boup... Je plaisante."
    ],
    // 3. VOTE OFF (En attente des résultats)
    vote_off: [
        "Les votes sont CLÔTURÉS !",
        "Les jeux sont faits...",
        "Merci de patienter un peu.",
        "Le podium va bientôt être révélé !",
        "Mais que fait la régie ?",
        "Allo la technique ? On s'endort ?",
        "Ils calculent à la main ou quoi ?",
        "Vous ne trouvez pas qu'ils sont longs ?",
        "Suspens insoutenable...",
        "Je parie que mon favori a gagné.",
        "Ça arrive, ça arrive...",
        "Je chauffe le processeur pour les résultats."
    ],
    // 4. PHOTOS LIVE
    photos: [
        "C'est le moment des photos !",
        "Ne m'oubliez pas !",
        "Je veux être sur la photo aussi !",
        "Un petit selfie ensemble ?",
        "Vous ne voulez pas me prendre en photo ?",
        "Allez, faites une grimace !",
        "Montrez vos plus beaux sourires.",
        "Envoyez vos photos, je les affiche !",
        "Je suis photogénique, non ?",
        "Attention le petit oiseau va sortir...",
        "On partage, on partage !"
    ]
};

// --- INITIALISATION THREE.JS ---
const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 1.5, 4); 

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// Lumières
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.5);
scene.add(hemiLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
dirLight.position.set(5, 10, 7.5);
scene.add(dirLight);

// --- CHARGEMENT DU MODÈLE ---
// Utilisez l'URL d'un modèle GLB public fiable (Robot "X Bot" de Mixamo est parfait pour ça)
const MODEL_URL = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/models/gltf/RobotExpressive/RobotExpressive.glb';

let mixer;
let animations = {};
let activeAction;
let model;

const loader = new GLTFLoader();
loader.load(MODEL_URL, function (gltf) {
    model = gltf.scene;
    scene.add(model);
    
    // Position du robot (centré bas)
    model.position.y = -2;
    model.scale.set(0.6, 0.6, 0.6); // Ajustez la taille si besoin

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
    // Si l'anim n'existe pas, on joue 'Idle' ou 'Wave' par défaut
    const animName = animations[name] ? name : 'Idle'; 
    const newAction = animations[animName];
    
    if (newAction !== activeAction) {
        if (activeAction) activeAction.fadeOut(duration);
        newAction.reset().fadeIn(duration).play();
        activeAction = newAction;
    }
}

// --- BULLE DE DIALOGUE ---
function showBubble(text, duration = 3000) {
    bubble.innerHTML = text;
    bubble.style.opacity = 1;
    bubble.style.transform = "translate(-50%, -20px) scale(1)";
    
    setTimeout(() => {
        bubble.style.opacity = 0;
        bubble.style.transform = "translate(-50%, 0) scale(0.8)";
    }, duration);
}

// --- CERVEAU DU ROBOT (Logique de comportement) ---
async function startBehaviorLogics() {
    
    // 1. SEQUENCE D'INTRO (Seulement si mode Accueil)
    if (config.mode === 'attente') {
        const sequence = DIALOGUES.intro;
        for (let step of sequence) {
            playAnim(step.action); // Wave, Talk, etc.
            showBubble(step.text, step.time - 500);
            await new Promise(r => setTimeout(r, step.time));
        }
        // Une fois l'intro finie, on passe en boucle aléatoire
        startRandomLoop('attente_loop');
    } 
    
    // 2. VOTE OFF
    else if (config.mode === 'vote_off') {
        playAnim('Idle'); 
        startRandomLoop('vote_off');
    }
    
    // 3. PHOTOS LIVE
    else if (config.mode === 'photos') {
        playAnim('Dance'); // Il danse pendant les photos !
        startRandomLoop('photos');
    }
    
    // 4. AUTRES CAS
    else {
        startRandomLoop('attente_loop');
    }
}

function startRandomLoop(categoryKey) {
    const phrases = DIALOGUES[categoryKey];
    
    // Boucle infinie de phrases aléatoires
    setInterval(() => {
        // 1 chance sur 3 de parler toutes les 6 secondes
        if (Math.random() > 0.3) {
            const text = phrases[Math.floor(Math.random() * phrases.length)];
            
            // Animation aléatoire quand il parle
            const actions = ['Talk', 'ThumbsUp', 'Wave', 'Yes'];
            const rndAction = actions[Math.floor(Math.random() * actions.length)];
            
            // Si on est en mode photo, on le laisse danser parfois
            if(config.mode === 'photos' && Math.random() > 0.5) {
                 // On ne change pas l'anim (Dance)
            } else {
                 playAnim(rndAction);
            }
            
            showBubble(text, 4000);
            
            // Retour à Idle (ou Dance) après avoir parlé
            setTimeout(() => {
                if(config.mode === 'photos') playAnim('Dance');
                else playAnim('Idle');
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

// Gestion redimensionnement
window.addEventListener('resize', onWindowResize, false);
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}
