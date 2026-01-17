import * as THREE from 'three';

const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

const MESSAGES_BAG = {
    attente: ["Bienvenue !", "Prêt pour le show ?", "Installez-vous bien !"],
    photos: ["Souriez ! 📸", "Clic-clac !", "Superbe photo !"],
    vote_off: ["C'est fini !", "Calcul des votes..."]
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchRobotFinal);
} else {
    launchRobotFinal();
}

function launchRobotFinal() {
    const old = document.querySelectorAll('[id^="robot-"]');
    old.forEach(el => el.remove());

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    canvas.style.cssText = `
        position: fixed !important; top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        z-index: 2147483647 !important; pointer-events: none !important;
        background: transparent !important;
    `;

    const bubble = document.createElement('div');
    bubble.id = 'robot-bubble-dynamic';
    document.body.appendChild(bubble);
    bubble.style.cssText = `
        position: fixed; opacity: 0; background: #000000; color: #FFFFFF;
        padding: 15px 25px; border-radius: 30px; font-family: Arial, sans-serif; 
        font-weight: bold; font-size: 20px; pointer-events: none; z-index: 2147483647;
        border: 2px solid #E2001A; box-shadow: 0 8px 20px rgba(0,0,0,0.8); text-align: center;
        transition: opacity 0.5s;
    `;

    initThreeJS(canvas, bubble);
}

function initThreeJS(canvas, bubble) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);

    scene.add(new THREE.AmbientLight(0xffffff, 1.8));
    const light = new THREE.DirectionalLight(0xffffff, 1.5);
    light.position.set(5, 5, 5);
    scene.add(light);

    // --- LE ROBOT ---
    const robotGroup = new THREE.Group();
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x050505 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1, 0.75);
    robotGroup.add(head);

    // Visage noir
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6);
    head.add(face);

    // Yeux (Néons)
    const eyeGeo = new THREE.TorusGeometry(0.12, 0.03, 8, 16, Math.PI);
    const eyeL = new THREE.Mesh(eyeGeo, neonMat);
    eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);

    // Sourire
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    // Corps
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    robotGroup.add(body);

    scene.add(robotGroup);

    // --- VARIABLES DE MOUVEMENT ---
    let time = 0, lastMsg = 0;
    let tx = 0, ty = 0, cx = 0, cy = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Déplacement aléatoire sur l'écran toutes les 5 secondes
        if (Math.round(time * 100) % 500 === 0) {
            tx = (Math.random() - 0.5) * 10; // Déplacement horizontal
            ty = (Math.random() - 0.5) * 5;  // Déplacement vertical
        }
        
        // Interpolation pour la fluidité (le robot glisse vers sa destination)
        cx += (tx - cx) * 0.01;
        cy += (ty - cy) * 0.01;

        // Application de la position + flottaison + rotation
        robotGroup.position.set(cx, cy + Math.sin(time * 2) * 0.25, 0);
        robotGroup.rotation.y = Math.sin(time * 0.5) * 0.3;
        robotGroup.rotation.z = Math.sin(time * 0.3) * 0.1;

        // Bulle de texte
        if (Date.now() - lastMsg > 7000) {
            const msgs = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
            bubble.innerText = msgs[Math.floor(Math.random() * msgs.length)];
            bubble.style.opacity = 1;
            lastMsg = Date.now();
            setTimeout(() => bubble.style.opacity = 0, 4000);
        }

        // Suivi de la bulle
        if (bubble.style.opacity == 1) {
            const p = robotGroup.position.clone();
            p.y += 1.6; p.project(camera);
            bubble.style.left = ((p.x * 0.5 + 0.5) * window.innerWidth - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = ((-p.y * 0.5 + 0.5) * window.innerHeight - bubble.offsetHeight - 20) + 'px';
        }
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
}
