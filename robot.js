import * as THREE from 'three';

const container = document.getElementById('robot-container');

if (container) {
    initRobot(container);
}

function initRobot(container) {
    let width = container.clientWidth;
    let height = container.clientHeight;
    if (height === 0) height = 500;

    // SCENE
    const scene = new THREE.Scene();
    // Pas de background ici, on laisse la transparence du CSS

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1.5, 7);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // ROBOT
    const robotGroup = new THREE.Group();
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Tête
    const headGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const head = new THREE.Mesh(headGeo, whiteMat);
    
    // Visage
    const faceGeo = new THREE.CircleGeometry(0.55, 32);
    const face = new THREE.Mesh(faceGeo, darkMat);
    face.position.set(0, 0, 0.71);
    head.add(face);

    // Yeux
    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.73);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.73);
    head.add(leftEye); head.add(rightEye);

    // Corps
    const bodyGeo = new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32);
    const body = new THREE.Mesh(bodyGeo, whiteMat);
    body.position.y = -0.9;

    // Bras
    function createArm(x) {
        const g = new THREE.Group();
        g.position.set(x, -0.7, 0);
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.2), blueMat);
        g.add(s);
        const a = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5), whiteMat);
        a.position.y = -0.3;
        g.add(a);
        return g;
    }
    const leftArm = createArm(-0.6);
    const rightArm = createArm(0.6);

    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(leftArm);
    robotGroup.add(rightArm);
    robotGroup.position.y = 0.5;
    scene.add(robotGroup);

    // ANIMATION
    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.05;
        robotGroup.position.y = 0.5 + Math.sin(time) * 0.1;
        rightArm.rotation.z = Math.cos(time * 3) * 0.5 + 0.5;
        renderer.render(scene, camera);
    }
    
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    });

    animate();
}
