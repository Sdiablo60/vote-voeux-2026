import * as THREE from 'three';

const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

const MESSAGES_BAG = {
    attente: ["Je suis là !", "Prêt pour le show ?", "Bienvenue à tous !"],
    photos: ["Souriez ! 📸", "Clic-clac !", "Superbe photo !"],
    vote_off: ["C'est fini !", "Calcul des votes..."]
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', launchRobotRescue);
} else {
    launchRobotRescue();
}

function launchRobotRescue() {
    // Nettoyage radical
    const old = document.querySelectorAll('[id^="robot-"]');
    old.forEach(el => el.remove());

    const canvas = document.createElement('canvas');
    canvas.id = 'robot-canvas-final';
    document.body.appendChild(canvas);

    // STYLE CRITIQUE : Z-index à 2 milliards pour passer devant tout
    canvas.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 2147483647 !important; 
        pointer-events: none !important;
        background: transparent !important;
        display: block !important;
    `;

    const bubble = document.createElement('div');
    bubble.id = 'robot-bubble-dynamic';
    document.body.appendChild(bubble);
    bubble.style.cssText = `
        position: fixed; opacity: 0; background: #000000 !important; color: #FFFFFF !important;
        padding: 15px 25px; border-radius: 30px; font-family: Arial, sans-serif; 
        font-weight: bold; font-size: 20px; pointer-events: none; z-index: 2147483647;
        border: 2px solid #E2001A; box-shadow: 0 8px 20px rgba(0,0,0,0.8); text-align: center;
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

    scene.add(new THREE.AmbientLight(0xffffff, 2.0));
    const light = new THREE.DirectionalLight(0xffffff, 1.5);
    light.position.set(5, 5, 5);
    scene.add(light);

    // --- LE ROBOT ---
    const robotGroup = new THREE.Group();
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1, 0.75);
    robotGroup.add(head);

    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6);
    head.add(face);

    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    robotGroup.add(body);

    scene.add(robotGroup);

    let time = 0, lastMsg = 0;
    let tx = 0, ty = 0, cx = 0, cy = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // Déplacement aléatoire
        if (Math.round(time * 100) % 400 === 0) {
            tx = (Math.random() - 0.5) * 8;
            ty = (Math.random() - 0.5) * 4;
        }
        cx += (tx - cx) * 0.01;
        cy += (ty - cy) * 0.01;

        robotGroup.position.set(cx, cy + Math.sin(time * 2) * 0.2, 0);
        robotGroup.rotation.y = Math.sin(time) * 0.2;

        // Parole
        if (Date.now() - lastMsg > 6000) {
            const msgs = MESSAGES_BAG[config.mode] || MESSAGES_BAG['attente'];
            bubble.innerText = msgs[Math.floor(Math.random() * msgs.length)];
            bubble.style.opacity = 1;
            lastMsg = Date.now();
            setTimeout(() => bubble.style.opacity = 0, 3000);
        }

        if (bubble.style.opacity == 1) {
            const p = robotGroup.position.clone();
            p.y += 1.5; p.project(camera);
            bubble.style.left = ((p.x * 0.5 + 0.5) * window.innerWidth - bubble.offsetWidth / 2) + 'px';
            bubble.style.top = ((-p.y * 0.5 + 0.5) * window.innerHeight - bubble.offsetHeight - 20) + 'px';
        }
        renderer.render(scene, camera);
    }
    animate();
}
