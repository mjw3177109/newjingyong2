// Map pointer coordinates using the same centered, square-cell geometry as the Canvas renderer.
import {BAMBOO_PASS} from './bamboo-pass.js';
export function bambooTileFromPointer(clientX,clientY,rect,canvasWidth,canvasHeight){
 if(!rect || ![rect.left,rect.top,rect.width,rect.height,canvasWidth,canvasHeight].every(Number.isFinite))return null;
 if(rect.width<=0||rect.height<=0||canvasWidth<=0||canvasHeight<=0)return null;
 if(!Number.isFinite(clientX)||!Number.isFinite(clientY))return null;
 const cell=Math.min(canvasWidth/BAMBOO_PASS.width,canvasHeight/BAMBOO_PASS.height);
 const ox=(canvasWidth-cell*BAMBOO_PASS.width)/2;
 const oy=(canvasHeight-cell*BAMBOO_PASS.height)/2;
 const px=(clientX-rect.left)*canvasWidth/rect.width;
 const py=(clientY-rect.top)*canvasHeight/rect.height;
 const x=Math.floor((px-ox)/cell),y=Math.floor((py-oy)/cell);
 if(x<0||y<0||x>=BAMBOO_PASS.width||y>=BAMBOO_PASS.height)return null;
 return {x,y};
}
