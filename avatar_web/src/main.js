import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(22, innerWidth / innerHeight, 0.1, 30);
camera.position.set(0, 1.35, 4.2);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setClearColor(0x000000, 0);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
document.getElementById('app').appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 2.3));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(1.5, 2.5, 3);
scene.add(key);

let vrm = null;
let currentExpression = 'neutral';
let speaking = false;
let mouthPhase = 0;
let nextBlinkAt = performance.now() + 2500;
let avatarBaseY = 0;
let chestBone = null;
const lookTarget = new THREE.Object3D();
lookTarget.position.set(0, 1.45, 2.5);
scene.add(lookTarget);

function setOnlyExpression(name, weight = 1) {
  if (!vrm?.expressionManager) return;
  const m = vrm.expressionManager;
  for (const n of ['happy','angry','sad','relaxed','surprised']) m.setValue(n, 0);
  if (name && name !== 'neutral') m.setValue(name, weight);
  currentExpression = name || 'neutral';
}

window.companionAvatar = {
  setExpression(name, weight = 1) { setOnlyExpression(name, weight); },
  setSpeaking(value) { speaking = !!value; },
  setLook(x, y) {
    lookTarget.position.set(Number(x) * 1.2, 1.45 + Number(y) * 0.7, 2.5);
    if (vrm?.lookAt) vrm.lookAt.target = lookTarget;
  },
  isReady() { return !!vrm; }
};

const loader = new GLTFLoader();
loader.register(parser => new VRMLoaderPlugin(parser));
loader.load('/model.vrm', gltf => {
  vrm = gltf.userData.vrm;
  VRMUtils.removeUnnecessaryVertices(gltf.scene);
  VRMUtils.combineSkeletons(gltf.scene);
  vrm.scene.traverse(obj => { obj.frustumCulled = false; });
  scene.add(vrm.scene);

  const box = new THREE.Box3().setFromObject(vrm.scene);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  vrm.scene.position.x -= center.x;
  vrm.scene.position.y -= box.min.y;
  avatarBaseY = vrm.scene.position.y;
  chestBone =
    vrm.humanoid?.getNormalizedBoneNode('upperChest') ??
    vrm.humanoid?.getNormalizedBoneNode('chest') ??
    null;
  camera.position.set(0, Math.max(1.0, size.y * 0.52), Math.max(3.0, size.y * 2.2));
  camera.lookAt(0, Math.max(0.9, size.y * 0.52), 0);
  if (vrm.lookAt) vrm.lookAt.target = lookTarget;
  setOnlyExpression('neutral');
  document.body.dataset.ready = 'true';
}, undefined, err => {
  console.error(err);
  document.body.dataset.error = String(err);
});

const clock = new THREE.Clock();
function animate(now) {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();

  if (vrm) {
    const m = vrm.expressionManager;
    if (m) {
      if (now >= nextBlinkAt) {
        m.setValue('blink', 1);
        setTimeout(() => {
          if (vrm?.expressionManager) vrm.expressionManager.setValue('blink', 0);
        }, 110);
        nextBlinkAt = now + 2500 + Math.random() * 3500;
      }

      for (const v of ['aa','ih','ou','ee','oh']) m.setValue(v, 0);
      if (speaking) {
        mouthPhase += dt * 9;
        const weight = 0.25 + 0.65 * Math.abs(Math.sin(mouthPhase));
        const seq = ['aa','ih','ou','ee','oh'];
        m.setValue(seq[Math.floor(mouthPhase) % seq.length], weight);
      }
    }
    const t = now * 0.001;
    vrm.scene.position.y = avatarBaseY + Math.sin(t * 1.7) * 0.004;
    if (chestBone) {
      chestBone.rotation.x = Math.sin(t * 1.7) * 0.008;
      chestBone.rotation.z = Math.sin(t * 0.65) * 0.004;
    }
    vrm.update(dt);
  }
  renderer.render(scene, camera);
}
requestAnimationFrame(animate);

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
