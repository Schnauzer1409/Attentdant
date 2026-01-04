interface ICaptureAreaProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
}

export default function CaptureArea({ videoRef, canvasRef }: ICaptureAreaProps) {
    return <>
        <video ref={videoRef} autoPlay playsInline className="w-full rounded-[10px] bg-black"/>
        <canvas ref={canvasRef} className="hidden" />
    </>
}