import argparse
import os
import imageio
import yaml


def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def get_initial_frame(idx, saved=True):
    conds = [depth[idx], canny_images[idx]]
    set_kv_to_none(pipe.unet)
    image_0 = pipe(
        prompt=prompt,
        image=conds,
        num_inference_steps=50,
        latents=latent,
        negative_prompt=negative_prompt,
        controlnet_conditioning_scale=[depth_controlnet_scale, canny_controlnet_scale],
        guidance_scale=guidance_scale,
        cross_attention_kwargs={
            "att_mode": "keep",
            "alpha": alpha
        },
    ).images[0]
    if saved:
        os.makedirs(f"{output_dir}", exist_ok=True)
        image_0.save(f"{output_dir}/{idx}.png")
    return image_0


def get_subsequent_frame(idx, saved=True):
    conds = [depth[idx], canny_images[idx]]

    move_index_to_zero(pipe.unet)

    image = pipe(
        prompt=prompt,
        image=conds,
        num_inference_steps=50,
        latents=latent,
        negative_prompt=negative_prompt,
        controlnet_conditioning_scale=[depth_controlnet_scale, canny_controlnet_scale],
        guidance_scale=guidance_scale,
        cross_attention_kwargs={
            "att_mode": "replace",
            "alpha": alpha
        },
    ).images[0]
    if saved:
        os.makedirs(f"{output_dir}", exist_ok=True)
        image.save(f"{output_dir}/{idx}.png")
    return image


def generate_video_sequence(start_idx=0):
    results = []
    images = get_initial_frame(start_idx)
    results.append(images)
    for i in range(start_idx + 1, len(depth)):
        idx = i
        move_index_to_zero(pipe.unet)
        images = get_subsequent_frame(idx)
        results.append(images)
    imageio.mimsave(
        f"{output_dir}/video.mp4",
        results, fps=movie_fps)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Load YAML configuration file.")
    parser.add_argument('config_path', help="Path to the YAML configuration file.")
    args = parser.parse_args()
    config = load_config(args.config_path)
    os.environ["CUDA_VISIBLE_DEVICES"] = str(config['system']['gpu_id'])

    from utils.utils_all import *
    from diffusers import (
        StableDiffusionXLControlNetPipeline,
        ControlNetModel,
        AutoencoderKL,
        DDIMScheduler
    )
    from diffusers.models import UNet2DConditionModel
    import torch
    from pytorch_lightning import seed_everything
    seed_everything(config['system']['seed'])

    canny_images = get_freestyle_images(f"{config['folders']['data']}/freestyle/")
    depth = get_depth_images(f"{config['folders']['data']}/depth/")

    prompt = config['prompt'] + ', realism, High quality, 8K, Realistic image'
    negative_prompt = "cartoon, anime, 3d, painting, monochrome, lowers, bad anatomy, worst quality, low quality"

    controlnets = [
        ControlNetModel.from_pretrained(
            config['model']['controlnet']['depth'],
            torch_dtype=torch.float16
        ),
        ControlNetModel.from_pretrained(
            config['model']['controlnet']['canny'],
            torch_dtype=torch.float16
        ),
    ]
    vae = AutoencoderKL.from_pretrained(config['model']['vae'], torch_dtype=torch.float16)
    scheduler = DDIMScheduler(beta_start=0.00085, beta_end=0.012, beta_schedule="scaled_linear", clip_sample=False,
                              set_alpha_to_one=True, steps_offset=1)
    if config['model']['unet']['is_local']:
        unet = UNet2DConditionModel.from_pretrained(config['model']['unet']['path'],
                                                torch_dtype=torch.float16)
    else:
        unet = UNet2DConditionModel.from_pretrained(config['model']['unet']['path'], subfolder="unet", torch_dtype=torch.float16)

    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        config['model']['pipe'],
        unet=unet, scheduler=scheduler, controlnet=controlnets, vae=vae, torch_dtype=torch.float16
    )

    from utils.Cross_Frame_Attention import Cross_Frame_Attention
    register_attention_control(pipe, Cross_Frame_Attention)
    # pipe.enable_model_cpu_offload()
    pipe.to('cuda')

    h, w = canny_images[0].size
    h, w = h // pipe.vae_scale_factor, w // pipe.vae_scale_factor
    latent = torch.randn((1, 4, w, h), dtype=torch.float16)
    movie_fps = config['movie']['fps']
    alpha = config['model']['alpha']
    guidance_scale = config['scale']['guidance']
    depth_controlnet_scale = config['scale']['depth_controlnet']
    canny_controlnet_scale = config['scale']['canny_controlnet']
    output_dir = os.path.join(config['folders']['output']['base'], config['folders']['output']['sub_folder'])
    generate_video_sequence()


