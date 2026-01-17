import * as THREE from 'three';

const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Installez-vous bien", "Ravi de vous voir !", "Ça va être génial !"],
    vote_off: ["Les jeux sont faits !", "On calcule tout ça...", "Qui va gagner ?", "Patience..."],
    photos: ["Ouistiti ! 📸", "Souriez pour la photo !", "Magnifique !", "Envoyez vos clichés !"],
    danse: ["Bougez avec moi ! 💃", "Quelle énergie !"]
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchFinalRobot);
} else {
    launchFinalRobot();
}

function launchFinalRobot() {
    const oldIds = ['robot-canvas-final', 'robot-bubble-dynamic'];
    oldIds.forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);
    canvas.style.cssText = `position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:2147483647; pointer-events:none; background:transparent;`;

    const bubble = document.createElement('div');
    bubble.id = 'robot-bubble-dynamic';
    document.body.appendChild(bubble);
    // CORRECTION COULEUR : Fond noir, texte blanc, bordure rouge
    bubble.style.cssText = `
        position: fixed; opacity: 0; background: #000000; color: #FFFFFF;
        padding: 15px 25px; border-radius: 30px; font-family: 'Arial', sans-serif; 
        font-weight: bold; font-size: 20px; pointer-events: none; z-index: 2147483647;
        transition: opacity 0.5s, transform 0.5s; transform: scale(0.8);
        border: 2px solid #E2001A; box-shadow: 0 8px 20px rgba(0,0,0,0.6); text-align: center;
    `;
    const arrow = document.createElement('div');
    arrow.style.cssText = `position:absolute; bottom:-10px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:10px solid transparent; border-right:10px solid transparent; border-top:10px solid #E2001A;`;
    bubble.appendChild(arrow);

    initThreeJS(canvas, bubble);
}

function initThreeJS(canvas, bubble) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- LE ROBOT ---
    const robotGroup = new THREE.Group();
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1, 0.75);
    robotGroup.add(head);

    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6);
    head.add(face);

    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.03, 8, 16, Math.PI), neonMat);
    eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);

    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    robotGroup.add(body);

    scene.add(robotGroup);

    // --- LOGIQUE DE DÉPLACEMENT ---
    let time = 0;
    let lastMsgTime = 0;
    // Variables pour le déplacement sur l'écran
    let targetX = 0, targetY = 0;
    let currentX = 0, currentY = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // 1. Mise à jour de la destination aléatoire toutes les 3 secondes
        if (Math.round(time * 100) % 300 === 0) {
            targetX = (Math.random() - 0.5) * 10; // Amplitude horizontale
            targetY = (Math.random() - 0.5) * 5;  // Amplitude verticale
        }

        // 2. Interpolation fluide vers la cible
        currentX += (targetX - currentX) * 0.01;
        currentY += (targetY - currentY) * 0.01;

        robotGroup.position.x = currentX;
        robotGroup.position.y = currentY + Math.sin(time * 2) * 0.2; // Flottaison bonus
        
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.3;
        robotGroup.rotation.z = Math.sin(time * 0.3) * 0.1;

        // 3. Bulle de texte
        if (Date.now() - lastMsgTime > 7000) {
            const msgs = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
            bubble.innerText = msgs[Math.floor(Math.random() * msgs.length)];
            bubble.appendChild(arrow);
            bubble.style.opacity = 1;
            bubble.style.transform = 'scale(1)';
            lastMsgTime = Date.now();
            setTimeout(() => { bubble.style.opacity = 0; bubble.style.transform = 'scale(0.8)'; }, 4000);
        }

        if (bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone();
            pos.y += 1.5; pos.project(camera);
            bubble.style.left = ((pos.x * 0.5 + 0.5) * width - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = ((-pos.y * 0.5 + 0.5) * height - bubble.offsetHeight - 20) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
