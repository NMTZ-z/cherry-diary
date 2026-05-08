# -*- coding: utf-8 -*-
"""
日记穿搭 & 姿态随机生成器 v4.0
基于日期种子伪随机，每天生成不同的穿搭+表情+动作组合

v4.0 优化（基于 Seedream 官方提示词指南 + 写实人像 Prompt 工程）：
1. 基准图: cherry_high_fashion_v4.png（唯一正确的基准图）
2. prompt 风格: 自然语言连贯段落，不再拼接关键词片段
3. reference weight: 0.85（面部一致性和创意的最佳平衡点）
4. 身材约束: 因果式曲线描述 + 衣服贴合度暗示，强化大胸表现
5. 全身构图: 低角度仰拍（相机膝盖高度），横屏全身入镜
6. 光线库: 升级为包含光源方向+光影效果的具体描述
7. 嘴唇安全: 锚定 "soft natural lips"，禁止咬唇等唇部形变动作
8. 质感修饰: 扩充精选词，强化写实感和背景虚化
9. 禁止: 相机型号参数、中文内容、重复描述基准图已有的五官特征

v3.3 → v4.0 变更摘要:
- _EXPRESSIONS: 删除"咬唇微笑"，替换为"轻抿微笑"
- _LIGHTINGS: 从笼统短语升级为含光源方向+效果的自然语言描述
- generate_prompt(): 从片段拼接改为连贯自然语言段落
- 身材: 从孤立形容词改为因果式曲线描述+衣服贴合暗示
- 构图: 加入低角度仰拍 + 横屏构图锚定
- 质感: 从3个词扩充到8个精选词
- 不动: _OUTFITS(60条), _ACTIONS(21条), _SCENES(20条)
"""

import random


class DiaryPromptGenerator:
    def __init__(self, date=None):
        from datetime import date as _date
        self.date = date or _date.today()
        random.seed(int(self.date.strftime("%Y%m%d")))

    _OUTFITS = {
        "elegant": [
            {"top": "burgundy velvet slip dress with deep V neckline", "hosiery": "black lace tights", "boots": "black pointed-toe over-the-knee leather boots with 12cm heels"},
            {"top": "champagne gold satin wrap dress with high thigh slit", "hosiery": "smoke gray sheer tights", "boots": "nude pointed-toe over-the-knee boots with 10cm heels"},
            {"top": "black silk backless long gown, open back to waist", "hosiery": "black 10-den ultra-sheer tights", "boots": "red patent leather over-the-knee boots with 11cm heels"},
            {"top": "white off-shoulder chiffon maxi dress with ruffle details", "hosiery": "white sheer tights", "boots": "silver buckle knee-high boots with 10cm heels"},
            {"top": "emerald green velvet halter dress with waist cutout", "hosiery": "black ultra-sheer tights", "boots": "black patent leather over-the-knee boots with 11cm heels"},
            {"top": "wine red silk camisole dress with lace trim sleeves", "hosiery": "wine red sheer tights", "boots": "gold pointed-toe over-the-knee boots with 12cm heels"},
            {"top": "navy blue satin off-shoulder gown with gradient tulle hem", "hosiery": "black sheer tights", "boots": "black suede over-the-knee boots with 11cm heels"},
            {"top": "blush pink chiffon maxi dress with sheer layered sleeves", "hosiery": "blush pink sheer tights", "boots": "nude knee-high boots with 10cm heels"},
            {"top": "black lace-paneled silk slip dress, lace covering bodice", "hosiery": "black lace pattern tights", "boots": "black pointed-toe over-the-knee boots with 12cm heels"},
            {"top": "deep purple velvet backless A-line dress", "hosiery": "black 10-den sheer tights", "boots": "deep purple patent over-the-knee boots with 11cm heels"},
            {"top": "pearl white satin halter evening gown, cinched waist", "hosiery": "white tulle tights", "boots": "white patent knee-high boots with 10cm heels"},
            {"top": "dark red silk qipao-style gown with high side slit", "hosiery": "black sheer tights", "boots": "black velvet over-the-knee boots with 12cm heels"},
            {"top": "gray satin slip dress with asymmetric diagonal cut bodice", "hosiery": "dark gray sheer tights", "boots": "silver gray over-the-knee boots with 11cm heels"},
            {"top": "black sheer lace long dress with silk camisole lining", "hosiery": "black lace pattern tights", "boots": "black knee-high boots with 10cm heels"},
            {"top": "cream white silk backless gown with pearl button details", "hosiery": "white ultra-sheer tights", "boots": "cream white over-the-knee boots with 11cm heels"},
            {"top": "deep blue off-shoulder silk gown with mermaid hem", "hosiery": "black sheer tights", "boots": "deep blue patent over-the-knee boots with 12cm heels"},
            {"top": "black silk halter high-slit gown with lace-up waist", "hosiery": "black sheer tights", "boots": "black patent over-the-knee boots with 11cm heels"},
            {"top": "champagne satin camisole backless gown with pearl chain waist", "hosiery": "champagne tulle tights", "boots": "nude knee-high boots with 10cm heels"},
            {"top": "wine red lace-paneled velvet gown with sheer lace long sleeves", "hosiery": "black lace pattern tights", "boots": "wine red over-the-knee boots with 11cm heels"},
            {"top": "emerald green silk slip dress with pearl strap details", "hosiery": "black ultra-sheer tights", "boots": "black suede over-the-knee boots with 12cm heels"},
        ],
        "casual": [
            {"top": "white crop top T-shirt, oversized drop shoulder", "hosiery": "white cotton tights", "boots": "cream white canvas high-top sneakers"},
            {"top": "oversized plaid shirt knotted at waist", "hosiery": "natural sheer tights", "boots": "brown lace-up ankle boots"},
            {"top": "black fitted crop tank top with high neckline", "hosiery": "black cotton tights", "boots": "black Chelsea boots, 3cm block heel"},
            {"top": "pink oversized hoodie", "hosiery": "white sheer tights", "boots": "pink chunky dad sneakers"},
            {"top": "denim overall dress with white lace camisole underneath", "hosiery": "light blue sheer tights", "boots": "white chunky canvas shoes"},
            {"top": "black off-shoulder top with puff sleeves", "hosiery": "black sheer tights", "boots": "black chunky ankle boots"},
            {"top": "red and white striped long-sleeve tee, tucked in", "hosiery": "natural sheer tights", "boots": "red canvas high-tops"},
            {"top": "white lace camisole crop top", "hosiery": "white sheer tights", "boots": "beige loafers with metal buckle"},
            {"top": "black fitted turtleneck short-sleeve tee", "hosiery": "black cotton tights", "boots": "black chunky sneakers"},
            {"top": "light blue oversized shirt, only two buttons fastened", "hosiery": "natural sheer tights", "boots": "white chunky sneakers"},
            {"top": "pink off-shoulder knit crop top with bell sleeves", "hosiery": "pink sheer tights", "boots": "pink canvas shoes"},
            {"top": "black mesh-paneled crop top", "hosiery": "black ultra-sheer tights", "boots": "black lace-up chunky boots"},
            {"top": "white sports crop top with black denim jacket draped over shoulders", "hosiery": "white cotton tights", "boots": "white chunky dad sneakers"},
            {"top": "beige loose knit cardigan over white camisole", "hosiery": "natural sheer tights", "boots": "brown flat loafers"},
            {"top": "black turtleneck crop top with plaid pleated skirt", "hosiery": "black cotton tights", "boots": "black chunky Chelsea boots"},
            {"top": "gray zip-up hoodie over white crop top", "hosiery": "gray sheer tights", "boots": "gray chunky dad sneakers"},
            {"top": "white puff-sleeve off-shoulder crop top", "hosiery": "white sheer tights", "boots": "white canvas high-tops"},
            {"top": "black fitted off-shoulder crop top, cinched hem", "hosiery": "black sheer tights", "boots": "black chunky ankle boots"},
            {"top": "pink cropped polo shirt", "hosiery": "pink sheer tights", "boots": "white canvas shoes"},
            {"top": "white cropped bomber jacket over black camisole", "hosiery": "black sheer tights", "boots": "black chunky sneakers"},
        ],
        "sexy": [
            {"top": "black leather dress with large cutouts at waist and sides", "hosiery": "black 10-den ultra-sheer tights", "boots": "black patent over-the-knee boots with 13cm heels"},
            {"top": "deep red latex fitted dress, high neck, long sleeves, glossy", "hosiery": "black lace pattern tights", "boots": "black patent over-the-knee boots with 12cm heels"},
            {"top": "black sheer lace bodysuit, full body lace coverage", "hosiery": "black lace pattern tights", "boots": "black pointed-toe over-the-knee boots with 12cm heels"},
            {"top": "white silk deep V nightgown with side slit to waist", "hosiery": "white ultra-sheer tights", "boots": "white patent over-the-knee boots with 11cm heels"},
            {"top": "silver sequin fitted mini dress, halter neck, open back", "hosiery": "silver sheer tights", "boots": "silver over-the-knee boots with 12cm heels"},
            {"top": "black strappy bondage dress with multiple crossing straps", "hosiery": "black ultra-sheer tights", "boots": "black pointed-toe knee-high boots with 13cm heels"},
            {"top": "red deep V fitted bandage mini dress, off-shoulder", "hosiery": "black lace pattern tights", "boots": "red patent over-the-knee boots with 12cm heels"},
            {"top": "black latex high-cut bodysuit, full coverage fitted", "hosiery": "black ultra-sheer tights", "boots": "black patent over-the-knee boots with 13cm heels"},
            {"top": "deep purple lace fitted dress with sheer effect", "hosiery": "black lace pattern tights", "boots": "deep purple over-the-knee boots with 12cm heels"},
            {"top": "gold sequin halter mini dress, deep V to waist", "hosiery": "black ultra-sheer tights", "boots": "gold patent over-the-knee boots with 12cm heels"},
            {"top": "black leather bustier crop top with leather mini skirt set", "hosiery": "black lace pattern tights", "boots": "black patent over-the-knee boots with 13cm heels"},
            {"top": "white sheer lace fitted long dress, high neck, long sleeves", "hosiery": "white lace pattern tights", "boots": "white over-the-knee boots with 12cm heels"},
            {"top": "black satin deep V fitted long gown, fully open back", "hosiery": "black ultra-sheer tights", "boots": "black velvet over-the-knee boots with 12cm heels"},
            {"top": "deep red leather fitted bodysuit with high-cut hem", "hosiery": "black lace pattern tights", "boots": "deep red patent over-the-knee boots with 13cm heels"},
            {"top": "black mesh-paneled leather fitted dress", "hosiery": "black ultra-sheer tights", "boots": "black pointed-toe knee-high boots with 12cm heels"},
            {"top": "silver fitted mini dress, high neck, reflective fabric", "hosiery": "black lace pattern tights", "boots": "silver patent over-the-knee boots with 13cm heels"},
            {"top": "black lace camisole fitted dress with sheer lace midsection", "hosiery": "black lace pattern tights", "boots": "black over-the-knee boots with 12cm heels"},
            {"top": "wine red silk deep V nightwear set, short robe with shorts", "hosiery": "wine red tulle tights", "boots": "wine red over-the-knee boots with 11cm heels"},
            {"top": "black leather corset top with leather shorts set", "hosiery": "black lace pattern tights", "boots": "black patent over-the-knee boots with 13cm heels"},
            {"top": "deep blue sequin deep V fitted mini dress", "hosiery": "black ultra-sheer tights", "boots": "deep blue patent over-the-knee boots with 12cm heels"},
        ],
        "cute": [
            {"top": "pink and white striped sailor top with large collar and bow", "hosiery": "white cotton tights", "boots": "brown round-toe lace-up knee-high boots with 5cm heel"},
            {"top": "light pink baby doll dress with puff sleeves and tutu skirt", "hosiery": "white tulle tights", "boots": "pink round-toe knee-high boots with 5cm heel"},
            {"top": "white lace ruffle off-shoulder crop top", "hosiery": "white sheer tights", "boots": "white round-toe knee-high boots with 5cm heel"},
            {"top": "mint green off-shoulder top with puff sleeves and ribbon", "hosiery": "white sheer tights", "boots": "white canvas high-tops"},
            {"top": "lavender baby doll dress with waist ribbon tie", "hosiery": "white tulle tights", "boots": "lavender round-toe knee-high boots with 5cm heel"},
            {"top": "pink ruffle camisole mini dress with tulle tutu skirt", "hosiery": "pink sheer tights", "boots": "pink round-toe ankle boots with 5cm heel"},
            {"top": "white navy stripe dress with double-breasted buttons", "hosiery": "white tulle tights", "boots": "blue round-toe knee-high boots with 4cm heel"},
            {"top": "cream yellow off-shoulder puff-sleeve crop top", "hosiery": "white sheer tights", "boots": "white canvas shoes"},
            {"top": "pink knit cardigan over white lace camisole", "hosiery": "white tulle tights", "boots": "pink round-toe knee-high boots with 4cm heel"},
            {"top": "blue denim overall dress with white striped shirt underneath", "hosiery": "white cotton tights", "boots": "white canvas high-tops"},
            {"top": "white lace mini dress with bodice bow", "hosiery": "white tulle tights", "boots": "white round-toe knee-high boots with 5cm heel"},
            {"top": "light pink off-shoulder crop tee with heart print", "hosiery": "pink sheer tights", "boots": "pink chunky sneakers"},
            {"top": "mint green tutu dress with ruffle waist and bow", "hosiery": "white tulle tights", "boots": "white round-toe ankle boots with 4cm heel"},
            {"top": "pink off-shoulder knit sweater with bell sleeves", "hosiery": "white sheer tights", "boots": "pink round-toe knee-high boots with 5cm heel"},
            {"top": "white lace-trim crop top with pink pleated mini skirt", "hosiery": "white tulle tights", "boots": "white canvas shoes"},
            {"top": "lavender puff-sleeve crop top with purple pleated skirt", "hosiery": "white sheer tights", "boots": "lavender round-toe knee-high boots with 5cm heel"},
            {"top": "yellow off-shoulder knit crop top with ruffle neckline", "hosiery": "white tulle tights", "boots": "yellow canvas shoes"},
            {"top": "pink peter pan collar crop top with pink plaid pleated skirt", "hosiery": "pink tulle tights", "boots": "pink round-toe knee-high boots with 4cm heel"},
            {"top": "white lantern-sleeve off-shoulder top with denim shorts", "hosiery": "white cotton tights", "boots": "white chunky sneakers"},
            {"top": "blue off-shoulder puff-sleeve A-line dress", "hosiery": "white tulle tights", "boots": "blue round-toe ankle boots with 5cm heel"},
        ],
        "professional": [
            {"top": "black fitted blazer over white silk shirt, two buttons undone", "hosiery": "black sheer tights", "boots": "black pointed-toe knee-high boots with 8cm heels"},
            {"top": "dark gray pencil skirt suit with fitted blazer", "hosiery": "black sheer tights", "boots": "black pointed-toe knee-high boots with 10cm heels"},
            {"top": "white silk shirt with black high-waisted wide-leg trousers", "hosiery": "black ultra-sheer tights", "boots": "black pointed-toe knee-high boots with 10cm heels"},
            {"top": "wine red fitted blazer dress with belt at waist", "hosiery": "black sheer tights", "boots": "wine red knee-high boots with 10cm heels"},
            {"top": "black silk shirt with black high-waisted straight trousers", "hosiery": "black sheer tights", "boots": "black patent knee-high boots with 10cm heels"},
            {"top": "beige blazer over black silk camisole with pencil skirt", "hosiery": "black sheer tights", "boots": "nude pointed-toe knee-high boots with 8cm heels"},
            {"top": "navy blue fitted blazer over white silk shirt", "hosiery": "black ultra-sheer tights", "boots": "navy blue knee-high boots with 10cm heels"},
            {"top": "black turtleneck fitted knit top with wide-leg trousers", "hosiery": "black sheer tights", "boots": "black pointed-toe knee-high boots with 8cm heels"},
            {"top": "white fitted blazer mini dress, cinched waist", "hosiery": "white sheer tights", "boots": "white pointed-toe knee-high boots with 10cm heels"},
            {"top": "gray blazer over black silk camisole with pencil skirt", "hosiery": "black sheer tights", "boots": "gray knee-high boots with 10cm heels"},
            {"top": "black silk shirt with high-waisted fitted pencil skirt", "hosiery": "black ultra-sheer tights", "boots": "black patent over-the-knee boots with 10cm heels"},
            {"top": "camel blazer with white silk shirt and straight trousers", "hosiery": "black sheer tights", "boots": "camel knee-high boots with 8cm heels"},
            {"top": "black slim blazer with black silk shirt, slight V-neck", "hosiery": "black sheer tights", "boots": "black pointed-toe knee-high boots with 10cm heels"},
            {"top": "white silk shirt with dark gray high-waisted pencil skirt", "hosiery": "black sheer tights", "boots": "black knee-high boots with 8cm heels"},
            {"top": "deep red blazer dress, V-neck cinched waist, knee-length", "hosiery": "black ultra-sheer tights", "boots": "deep red knee-high boots with 10cm heels"},
            {"top": "black high-neck silk top with high-waisted wide-leg trousers", "hosiery": "black sheer tights", "boots": "black patent knee-high boots with 10cm heels"},
            {"top": "cream white blazer over black silk camisole with pencil skirt", "hosiery": "black sheer tights", "boots": "cream white knee-high boots with 8cm heels"},
            {"top": "dark navy slim blazer with white silk shirt and straight trousers", "hosiery": "black sheer tights", "boots": "navy blue knee-high boots with 10cm heels"},
            {"top": "black V-neck blazer dress with high side slit", "hosiery": "black ultra-sheer tights", "boots": "black pointed-toe over-the-knee boots with 10cm heels"},
            {"top": "gray slim blazer with black silk shirt and black pencil skirt", "hosiery": "black sheer tights", "boots": "gray knee-high boots with 10cm heels"},
        ],
    }

    _EXPRESSIONS = [
        ("甜美微笑", "a bright open smile showing a hint of upper teeth, eyes warm and locked on camera"),
        ("浅笑", "lips barely curved in a faint smile, eyes calm and steady on the camera"),
        ("害羞低头微笑", "eyes cast down shyly with a blush on cheeks, then lifting gaze to meet the camera with a timid smile"),
        ("自信直视", "chin slightly raised, a confident knowing smile, eyes sharp and direct into the camera"),
        ("慵懒迷离", "half-lidded relaxed eyes with a dazed hazy look, soft smile, gaze drifting toward camera"),
        ("温柔注视", "soft tender eyes full of warmth, gentle caring smile, eyes fixed on the viewer"),
        ("歪头微笑", "head tilted to one side, curious bright smile, eyes playful and on the camera"),
        ("轻抿微笑", "lips pressed together in a restrained smile, eyes narrowed slightly with amusement, looking at camera"),
        ("认真注视", "focused intent eyes, calm composed expression, steady gaze into the camera"),
        ("温柔浅笑", "eyes soft and relaxed, a quiet serene smile, gaze gently on the camera"),
        ("撩发妩媚", "a teasing sidelong glance with one eyebrow raised, a subtle smirk, eyes catching the camera"),
        ("慵懒自然", "completely relaxed face, mouth slightly open, sleepy content eyes looking at camera"),
        ("若有所思", "eyes gazing upward briefly then returning to camera, lips in a slight unconscious pout"),
        ("傲娇微笑", "chin up with a playful defiant smirk, both eyebrows raised, eyes challenging the camera"),
        ("回眸浅笑", "looking back over shoulder, a sweet smile, eyes meeting the camera from the side"),
        ("安静恬淡", "serene peaceful eyes, lips in a natural resting position, calm quiet gaze at camera"),
        ("微微鼓腮", "cheeks slightly puffed in a pouty face, round innocent eyes looking at camera"),
        ("天真灿烂", "a wide happy grin with crinkled eyes, radiating joy, bright eyes on the camera"),
        ("似笑非笑", "lids lowered in a mysterious half-smile, one corner of mouth slightly raised, eyes holding the camera gaze"),
        ("含情脉脉", "heavy-lidded warm eyes with a tender loving look, lips barely parted, gaze deep into the camera"),
    ]

    _ACTIONS = [
        ("自然站立", "standing naturally facing camera with arms relaxed at sides"),
        ("重心偏移站立", "standing with weight shifted to one hip, arms casually at sides"),
        ("单手叉腰", "standing with one hand resting on hip, the other arm hanging loosely"),
        ("双手背后", "standing with both hands clasped behind her back in a relaxed posture"),
        ("双手交叉身前", "standing with hands loosely clasped in front of her waist"),
        ("自然走路", "walking toward camera with arms swinging naturally, caught mid-step"),
        ("侧身站立", "standing in a relaxed three-quarter pose, body slightly turned"),
        ("坐沙发扶手", "sitting on a sofa armrest with legs crossed, one hand resting on the cushion"),
        ("坐床边", "sitting on the edge of a bed with legs dangling, hands resting on the mattress"),
        ("坐窗台", "sitting on a wide windowsill with legs tucked up, arms wrapped around her knees"),
        ("坐地毯", "sitting on a soft carpet with legs folded to one side, hands resting in her lap"),
        ("坐高脚凳", "perched on a bar stool with legs crossed, forearms resting on the counter"),
        ("坐椅子", "sitting in an armchair with legs crossed, hands draped over the armrests"),
        ("坐梳妆台", "seated at a vanity table, one hand lightly touching the dressing surface"),
        ("靠墙站立", "leaning back against a wall with arms relaxed, shoulders at ease"),
        ("倚门框", "leaning casually against a doorframe with arms loosely crossed"),
        ("靠窗边", "standing by a window with her shoulder against the frame, gazing outside"),
        ("靠栏杆", "leaning forward on a balcony railing with forearms resting on the rail"),
        ("侧卧沙发", "lying on her side on a plush sofa, head propped up on her hand"),
        ("侧躺床上", "lying on her side on a bed, one arm tucked under her head"),
        ("趴在床上", "lying on her stomach on a bed with chin resting on folded hands, ankles crossed"),
    ]

    _SCENES = [
        "a luxury hotel suite with warm ambient lighting and elegant furnishings",
        "a cozy bedroom with warm lighting, plush bedding, and a wooden headboard",
        "a spacious living room with floor-to-ceiling windows overlooking a city view",
        "a hotel bathroom vanity area with warm mirror lights and marble surfaces",
        "a walk-in closet with soft warm lighting and mirrored wardrobe doors",
        "a bedroom with a full-length mirror and a warm glowing table lamp",
        "a balcony at golden hour with warm sunset light casting long shadows, city skyline in background",
        "a vanity area with neatly arranged cosmetics and a warm glowing table lamp",
        "a luxury hotel lobby lounge with plush sofas and warm ambient tones",
        "a dressing room with soft flattering warm lighting and a large mirror",
        "a bedroom beside a large window with warm golden sunlight flooding through curtains",
        "a hotel room with elegant dark wood furniture and warm ambient mood lighting",
        "a living room with marble surfaces, a warm floor lamp, and soft textures",
        "a hotel corridor with warm wall sconces casting soft light on patterned carpet",
        "a bedroom with sheer curtains billowing in a gentle breeze, golden afternoon light",
        "a luxury apartment living area with panoramic city skyline visible at dusk",
        "a boutique hotel room with plush furnishings, soft textures, and warm tones",
        "a sunlit room with warm golden hour glow streaming through tall windows",
        "a stylish hotel suite with warm ambient mood lighting, dark wood accents, and fresh flowers",
        "a cozy room with soft blankets draped on a sofa, warm lamp light, and a small flower vase on a side table",
    ]

    _LIGHTINGS = [
        "soft natural window light from the left casting gentle shadows across her face and body, creating a warm glow on her skin",
        "late afternoon golden sunlight streaming through sheer curtains from the right, wrapping her in a warm amber glow with soft shadows",
        "warm ambient room lighting with a soft directional light from above-left, creating gentle shadows that sculpt her facial contours",
        "golden hour sunlight pouring through a large window behind her, creating a warm rim light around her silhouette with soft front fill",
        "a warm floor lamp to her right casting a cozy upward glow, mixed with soft diffused daylight from a distant window on the left",
        "soft overcast daylight filtering through sheer white curtains, providing even flattering illumination across her entire figure",
        "warm sconce lighting from both sides creating a balanced soft glow, with gentle shadows defining her curves and facial structure",
        "morning sunlight from a window behind the camera, illuminating her face directly while casting long soft shadows behind her",
        "a mix of warm golden artificial light and cool natural window light from the left, creating subtle two-tone illumination on her skin",
        "soft warm backlight from a window behind her, with gentle reflected light filling in her face and front, creating a dreamy halo effect",
    ]

    _ACCESSORIES = [
        "silver pendant necklace", "pearl drop earrings", "black choker necklace",
        "delicate gold bracelet", "sparkling pendant necklace", "small chain-strap bag",
        "pearl bracelet", "butterfly earrings", "elegant brooch", "flower stud earrings",
        "metallic bangle", "ribbon hair tie",
    ]

    _MAKEUPS = [
        "natural makeup with soft pink lips",
        "subtle smoky eye with nude lips",
        "sweet blush makeup with glossy pink lips",
        "bold red lip with classic winged liner",
        "natural no-makeup look with nude lips",
        "Korean glass skin makeup with gradient lips",
        "vintage red lip makeup",
        "soft peach makeup with coral blush",
        "glamour shimmery eye makeup",
        "warm bronzed makeup with peach lips",
        "honey peach makeup with warm tones",
        "refined daily makeup with rosy lips",
        "fresh dewy makeup with coral lips",
        "gentle elegant makeup with milky tea lips",
        "soft romantic makeup with berry-stained lips",
    ]

    DEFAULT_REF_WEIGHT = 0.85

    def generate_prompt(self, ref_weight=None):
        theme = random.choice(list(self._OUTFITS.keys()))
        outfit = random.choice(self._OUTFITS[theme])
        expression_cn, expression_en = random.choice(self._EXPRESSIONS)
        action_cn, action_en = random.choice(self._ACTIONS)
        scene = random.choice(self._SCENES)
        lighting = random.choice(self._LIGHTINGS)
        accessory = random.choice(self._ACCESSORIES)
        makeup = random.choice(self._MAKEUPS)
        weight = ref_weight if ref_weight is not None else self.DEFAULT_REF_WEIGHT

        # v4.0: 自然语言连贯段落，不再拼接关键词片段
        prompt = (
            f"The same woman from the reference photo. "
            f"Full body shot from a low camera angle, as if the photographer is kneeling at her knee level, "
            f"looking up at her. Her entire figure from head to toe is fully visible within the wide horizontal frame, "
            f"with natural breathing space on both sides. "
            f"She has a curvaceous hourglass figure with a very full voluptuous bust, narrow waist, and wide hips. "
            f"Her outfit clings tightly to her curves, accentuating her full bust and feminine silhouette. "
            f"She wears {outfit['top']}, {outfit['hosiery']}, and {outfit['boots']}. "
            f"{action_en}, {expression_en}. Soft natural lips. "
            f"{accessory}, {makeup}. "
            f"The scene is {scene}. {lighting}. "

            f"Soft-focus background with shallow depth of field, "
            f"natural skin texture with visible pores, "
            f"accentuated feminine curves, "
            f"photorealistic, sharp focus, "
            f"candid fashion photography feel, "
            f"true-to-life colors, film-like quality."
        )

        return {
            "theme": theme,
            "top": outfit["top"],
            "hosiery": outfit["hosiery"],
            "boots": outfit["boots"],
            "expression": expression_cn,
            "action": action_cn,
            "ref_weight": weight,
            "prompt": prompt,
        }


if __name__ == "__main__":
    gen = DiaryPromptGenerator()
    result = gen.generate_prompt()
    print(f"Theme: {result['theme']}")
    print(f"Expression: {result['expression']}")
    print(f"Action: {result['action']}")
    print(f"Ref Weight: {result['ref_weight']}")
    print(f"\nPrompt ({len(result['prompt'])} chars):")
    print(result['prompt'])