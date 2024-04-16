import torch
from diffusers.models.attention_processor import Attention


class Cross_Frame_Attention:
    r"""
      Processor for managing attention mechanisms in neural network models, specifically designed
      for handling sequences of images or video frames. This class is tailored for scenarios where
      the attention from the initial frame needs to be preserved or altered throughout a sequence
      of frames, such as in video generation or frame-by-frame image processing.

      The processor supports different attention modes, including 'keep' and 'replace', which
      determine how attention weights and values from the initial frame are retained or modified
      in subsequent frames. This functionality is crucial for tasks that require consistency
      and temporal coherence across frames, such as stable video generation.

      Attributes:
          k (list): Stores the keys for the attention mechanism from each frame.
          v (list): Stores the values for the attention mechanism from each frame.
          index (int): Tracks the current frame index in the sequence.
          forever_keep (bool): Determines whether the initial frame's attention is always
                               kept throughout the sequence.

      The processor integrates with attention layers in neural networks and modifies the attention
      weights and values based on the specified mode and the current frame in the sequence.
      """

    def __init__(self, forever_keep=None):
        self.k = []
        self.v = []
        self.index = 0
        self.forever_keep = forever_keep

    def __call__(
            self,
            attn: Attention,
            hidden_states,
            encoder_hidden_states=None,
            attention_mask=None,
            temb=None,
            scale: float = 1.0,
            **cross_attention_kwargs
    ):
        self.alpha = cross_attention_kwargs['alpha']
        self.tensor_device = hidden_states.device

        assert cross_attention_kwargs['att_mode'] in ["replace", "keep"]

        residual = hidden_states

        if attn.spatial_norm is not None:
            hidden_states = attn.spatial_norm(hidden_states, temb)

        input_ndim = hidden_states.ndim

        if input_ndim == 4:
            batch_size, channel, height, width = hidden_states.shape
            hidden_states = hidden_states.view(batch_size, channel, height * width).transpose(1, 2)

        batch_size, sequence_length, _ = (
            hidden_states.shape if encoder_hidden_states is None else encoder_hidden_states.shape
        )

        if attn.group_norm is not None:
            hidden_states = attn.group_norm(hidden_states.transpose(1, 2)).transpose(1, 2)

        query = attn.to_q(hidden_states, scale=scale)

        if encoder_hidden_states is None:
            encoder_hidden_states = hidden_states
        elif attn.norm_cross:
            encoder_hidden_states = attn.norm_encoder_hidden_states(encoder_hidden_states)

        self_key = attn.to_k(encoder_hidden_states, scale=scale)
        self_value = attn.to_v(encoder_hidden_states, scale=scale)

        if not self.forever_keep:
            if cross_attention_kwargs['att_mode'] == "keep":
                key = attn.to_k(encoder_hidden_states,
                                scale=scale)
                value = attn.to_v(encoder_hidden_states,
                                  scale=scale)

                inner_dim = key.shape[-1]
                head_dim = inner_dim // attn.heads
                query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
                key = key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
                value = value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)

                self.k.append(key.to("cpu"))
                self.v.append(value.to("cpu"))
            else:
                assert self.k is not None and self.v is not None
                key = self.k[self.index].to(query.device)

                value = self.v[self.index].to(query.device)

                inner_dim = self_key.shape[-1]
                head_dim = inner_dim // attn.heads

                query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)

                self_key = self_key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
                self_value = self_value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
                self_key = self.alpha * self_key
                key = torch.cat((self_key, key), dim=2)
                value = torch.cat((self_value, value), dim=2)

                self.index = self.index + 1
        else:
            key = attn.to_k(encoder_hidden_states, scale=scale)
            value = attn.to_v(encoder_hidden_states, scale=scale)
            inner_dim = key.shape[-1]
            head_dim = inner_dim // attn.heads
            query = query.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
            key = key.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)
            value = value.view(batch_size, -1, attn.heads, head_dim).transpose(1, 2)

        hidden_states = torch.nn.functional.scaled_dot_product_attention(
            query, key, value, attn_mask=attention_mask, dropout_p=0.0, is_causal=False
        )

        hidden_states = hidden_states.transpose(1, 2).reshape(batch_size, -1, attn.heads * head_dim)
        hidden_states = hidden_states.to(query.dtype)

        hidden_states = attn.to_out[0](hidden_states, scale=scale)
        hidden_states = attn.to_out[1](hidden_states)

        if input_ndim == 4:
            hidden_states = hidden_states.transpose(-1, -2).reshape(batch_size, channel, height, width)

        if attn.residual_connection:
            hidden_states = hidden_states + residual

        hidden_states = hidden_states / attn.rescale_output_factor

        return hidden_states
