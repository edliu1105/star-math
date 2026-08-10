# -*- coding: utf-8 -*-
"""生成 codex 素材批次指令文件。"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "batches")
os.makedirs(OUT, exist_ok=True)

STYLE = ("cute chibi 2D cartoon sticker illustration for a toddler learning app, "
         "bold clean uniform black outlines, flat vibrant saturated colors with soft cel shading, "
         "big friendly expressive eyes, rounded child-safe shapes, cheerful happy expression, "
         "high-quality children picture-book style, the figure fills about 85% of the frame and is centered "
         "with a small even margin, SOLID PURE WHITE background (#FFFFFF), no ground shadow, no gradient background, "
         "no text, no letters, no watermark, no border, no frame")

BG_STYLE = ("bright cheerful 2D cartoon background illustration for a toddler learning app, "
            "flat vibrant saturated colors with soft cel shading, clean simple shapes, "
            "children picture-book style, wide open uncluttered composition with plenty of empty space "
            "in the middle and lower area so that characters can be placed on top later, "
            "no text, no letters, no watermark, no border, no frame, NO characters, NO people, NO animals")

CHARS = [
 # 西游记
 ("wukong", "a cute cartoon monkey warrior boy, golden-yellow furry face with peach-pink cheeks, wearing a yellow monk shirt with a red vest and a tiger-stripe skirt, a golden circlet headband on his forehead with two long red feather plumes, holding a golden staff with red ends, a small monkey tail, mischievous confident grin, standing full body facing viewer"),
 ("tangseng", "a cute cartoon gentle young monk man, kind round face, shaved head under a tall golden five-panel crown hat, wearing a red and gold ceremonial monk robe over a beige inner robe, palms pressed together in a peaceful greeting, serene kind smile, standing full body facing viewer"),
 ("bajie", "a cute cartoon chubby pig man, pale pink skin, big floppy pig ears and a wide snout, wearing a simple blue-grey monk robe over a round belly, holding a nine-tooth rake tool over one shoulder, silly happy grin, standing full body facing viewer"),
 ("shaseng", "a cute cartoon calm monk man with a tanned face and a short dark beard, wearing a brown-yellow monk robe, a necklace of large round beads, holding a monk crescent spade staff, gentle loyal expression, standing full body facing viewer"),
 ("bailongma", "a cute cartoon little white pony horse, pure white coat, flowing pale-blue mane and tail, a small red and gold saddle and bridle, big gentle eyes, standing in side view with the head turned toward the viewer, friendly"),
 # 葫芦娃
 ("hulu1", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT RED leaf vest and a BRIGHT RED leaf skirt, a BRIGHT RED gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu2", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT ORANGE leaf vest and a BRIGHT ORANGE leaf skirt, a BRIGHT ORANGE gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu3", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT YELLOW leaf vest and a BRIGHT YELLOW leaf skirt, a BRIGHT YELLOW gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu4", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT GRASS GREEN leaf vest and a BRIGHT GRASS GREEN leaf skirt, a BRIGHT GRASS GREEN gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu5", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT CYAN TEAL leaf vest and a BRIGHT CYAN TEAL leaf skirt, a BRIGHT CYAN TEAL gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu6", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT BLUE leaf vest and a BRIGHT BLUE leaf skirt, a BRIGHT BLUE gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("hulu7", "a cute cartoon chibi boy hero with black bowl-cut hair, wearing a BRIGHT PURPLE leaf vest and a BRIGHT PURPLE leaf skirt, a BRIGHT PURPLE gourd-shaped hat with a small green stem on his head, bare arms and bare feet, brave determined smile, standing with fists ready, facing viewer"),
 ("yeye", "a cute cartoon kind old grandfather farmer, long white beard and bushy white eyebrows, bald on top with white hair on the sides, wearing a simple brown-green Chinese peasant robe, holding a wooden walking stick, warm gentle smile, standing full body facing viewer"),
 ("shejing", "a cute NON-SCARY friendly cartoon snake lady character, pale mint-green skin, long black hair with a green headband, wearing a green scaly dress, a soft rounded cartoon snake tail instead of legs, playful cheeky smirk, completely child-friendly and not frightening"),
 ("xiezijing", "a cute NON-SCARY friendly cartoon scorpion character standing upright, purple-blue rounded body, two big round friendly eyes, two small soft cartoon claws and a curled tail with a rounded harmless tip, wearing a small purple cape, cheeky grin, completely child-friendly and not frightening"),
 # 复联
 ("ironman", "a cute cartoon armored hero in a red and gold metal suit, a glowing round light-blue circle on the chest, a sleek red and gold helmet with two glowing light-blue rectangular eye slits, standing confidently with hands on hips, full body facing viewer"),
 ("cap", "a cute cartoon hero in a blue uniform with red and white vertical stripes across the belly, a big white star on the chest, a blue helmet with a small white wing on each side, holding a large round shield with red and white concentric rings and a white star in the center, full body facing viewer"),
 ("thor", "a cute cartoon thunder hero, long blonde hair and a short blonde beard, silver armor with round metal discs on the chest, a long flowing red cape, holding a short-handled square stone hammer, friendly heroic smile, full body facing viewer"),
 ("hulkman", "a cute cartoon big friendly green muscular giant, bright green skin, messy black hair, torn purple shorts, no shirt, huge round arms, big goofy friendly grin, not scary at all, full body facing viewer"),
 ("widow", "a cute cartoon spy heroine, wavy red-orange shoulder-length hair, a black tactical bodysuit with a silver belt buckle, black gloves and boots, confident friendly smile, full body facing viewer"),
 ("hawkeye", "a cute cartoon archer hero, short brown hair, a dark purple and black tactical vest, a quiver of arrows on his back, holding a bow in one hand, one eye winking, friendly smile, full body facing viewer"),
 ("spider", "a cute cartoon spider hero in a red and blue full bodysuit with a thin black web pattern, large white teardrop-shaped eye lenses outlined in black, a small black spider emblem on the chest, playful crouching pose, full body facing viewer"),
 ("spiderblack", "a cute cartoon spider hero in a BLACK bodysuit with BRIGHT RED web pattern lines and red palms, large white teardrop-shaped eye lenses outlined in black, a red spider emblem on the chest, cool playful pose, full body facing viewer"),
 # 汪汪队
 ("ryder", "a cute cartoon boy about ten years old, short brown hair, wearing a blue and red vest jacket with a round badge, blue jeans and red sneakers, holding a small tablet device, confident friendly smile, full body facing viewer"),
 ("chase", "a cute cartoon german shepherd puppy standing upright on two legs, brown and tan fur, wearing a dark blue police cap and a dark blue vest uniform with a silver badge, one paw raised in a cheerful salute, facing viewer"),
 ("marshall", "a cute cartoon dalmatian puppy standing upright on two legs, white fur with black spots, wearing a red firefighter helmet and a red vest with a flame badge, clumsy happy grin, facing viewer"),
 ("skye", "a cute cartoon cockapoo puppy girl standing upright on two legs, light golden-cream fluffy fur, wearing a pink flight helmet with goggles on top and a pink pilot vest with a wings badge, cheerful waving paw, facing viewer"),
 ("rubble", "a cute cartoon english bulldog puppy standing upright on two legs, tan and cream fur, wearing a yellow construction hard hat and a yellow vest with a shovel badge, tough happy grin, facing viewer"),
 ("zuma", "a cute cartoon chocolate labrador puppy standing upright on two legs, brown fur, wearing an orange life vest with a fish badge and an orange diving cap, relaxed happy smile, facing viewer"),
 ("rocky", "a cute cartoon grey and white mixed-breed puppy standing upright on two legs, wearing a green vest with a recycling arrows badge and a green cap, holding a small screwdriver, cheerful smile, facing viewer"),
 # Bluey
 ("bluey", "a cute cartoon blue heeler cattle dog puppy girl standing upright on two legs, light blue fur with darker blue patches on the head and back, a cream-colored muzzle and belly, floppy triangular ears, a short tail, big happy smile, facing viewer"),
 ("bingo", "a cute cartoon red heeler cattle dog puppy girl standing upright on two legs, warm orange-tan fur with a cream-colored muzzle and belly, floppy triangular ears, slightly smaller and rounder body, sweet happy smile, facing viewer"),
 ("bandit", "a cute cartoon adult male blue heeler cattle dog dad standing upright on two legs, blue-grey fur with darker patches, a cream muzzle, tall and lanky friendly build, warm dad smile, facing viewer"),
 ("chilli", "a cute cartoon adult female red heeler cattle dog mum standing upright on two legs, warm orange-tan fur with a cream muzzle, gentle warm mum smile, facing viewer"),
 # 佩奇
 ("peppa", "a happy little pink cartoon pig girl standing, wearing a simple red dress, a round pink head, a small snout, two round eyes, rosy cheeks, thin arms and legs, tiny black shoes, facing viewer"),
 ("george", "a happy little pink cartoon pig toddler boy standing, wearing a simple blue shirt and blue shorts, a round pink head, a small snout, two round eyes, holding a small green toy dinosaur in one hand, tiny black shoes, facing viewer"),
 ("daddypig", "a cute cartoon big pink pig dad with a round belly, wearing a teal-green shirt and dark trousers, round black glasses, a short dark stubble beard on his chin, jolly friendly smile, facing viewer"),
 ("mummypig", "a cute cartoon pink pig mum, wearing a simple orange dress, long dark eyelashes, a gentle warm smile, facing viewer"),
]

PROPS = [
 ("star", "a plump cheerful five-pointed star, shiny golden yellow with a lighter yellow highlight, soft warm glow around it, no face"),
 ("gubang_seg", "a plain horizontal golden metal rod segment, a smooth polished gold cylinder with a bright highlight stripe along the top, perfectly flat vertical ends on the left and right so it can be tiled seamlessly side by side, no decoration, no caps"),
 ("gubang_tip", "the right end cap of a golden magic staff, a short gold cylinder ending in a rounded red and gold cap on the right side, flat vertical cut on the left side"),
 ("stone", "a cute cartoon round grey stepping stone in shallow water, a flat oval top surface seen from a slightly high angle, a little green moss on one edge, small water ripples around the base"),
 ("gourd_r", "a cute cartoon calabash gourd fruit, shiny BRIGHT RED skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_o", "a cute cartoon calabash gourd fruit, shiny BRIGHT ORANGE skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_y", "a cute cartoon calabash gourd fruit, shiny BRIGHT YELLOW skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_g", "a cute cartoon calabash gourd fruit, shiny BRIGHT GRASS GREEN skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_c", "a cute cartoon calabash gourd fruit, shiny BRIGHT CYAN TEAL skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_b", "a cute cartoon calabash gourd fruit, shiny BRIGHT BLUE skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("gourd_p", "a cute cartoon calabash gourd fruit, shiny BRIGHT PURPLE skin, classic double-bulb gourd shape, a short green stem with one small green leaf and a curly tendril on top"),
 ("turtle", "a cute tiny cartoon baby sea turtle seen from a high three-quarter angle, a rounded green shell with lighter green hexagon patches, four little flippers, a small head with big friendly eyes"),
 ("icecream", "a cute cartoon single round scoop of pink strawberry ice cream sitting in a golden waffle cone"),
 ("cookie", "a cute cartoon round golden-brown chocolate chip cookie with dark brown chips, seen from directly above"),
 ("mudblob", "a cute cartoon splash of brown mud, an irregular rounded splat blob shape with three small separate droplets around it"),
 ("goon", "a cute NON-SCARY cartoon robot minion, a small rounded purple-grey metal body, one big round friendly eye in the middle, two little arms and two tiny legs, a silly harmless expression, completely child-friendly"),
 ("web", "a small cute cartoon sticky white spider web blob, a rounded splat of white silk threads"),
 ("portal", "a cute cartoon glowing circular magic portal ring seen from the front, a bright orange-yellow energy ring with swirling golden sparks inside, a dark warm center"),
 ("quinjet", "a cute cartoon small grey stealth jet aircraft seen from a front three-quarter angle, swept-back wings, two glowing light-blue engines, chunky toy-like proportions"),
 ("peach", "a cute cartoon pink and yellow peach fruit with a small green leaf on top"),
 ("basket", "a cute cartoon empty woven wicker basket seen from the front, warm brown straw weave, a curved handle"),
]

BGS = [
 ("bg_sky", "a magical calm night sky, a deep indigo and purple gradient sky filled with many small golden stars, soft glowing pink and blue nebula clouds, a few dark rounded floating grassy island silhouettes along the bottom edge, dreamy and peaceful"),
 ("bg_monkey", "a bright Chinese mountain landscape, a calm blue river running horizontally across the middle of the image from left to right, green rounded mountains with pink peach blossom trees on both banks, a small waterfall in the distance, sunny sky with fluffy white clouds"),
 ("bg_hulu", "a misty green Chinese mountain cliff scene, a thick climbing vine plant with big green leaves stretching horizontally across the upper third of the image, a dark cave entrance on the far left, a rocky summit path on the far right, sunny sky, no fruit on the vine"),
 ("bg_aveng", "the rooftop helipad of a tall modern glass skyscraper at golden sunset, a large flat circular landing pad in the middle of the roof, a city skyline of skyscrapers in the distance, warm orange sky"),
 ("bg_paw", "a cheerful seaside bay, a wide sandy beach across the whole foreground, calm blue sea behind it, a red and white lighthouse and small colorful houses on a green hill in the distance, sunny blue sky"),
 ("bg_bluey", "a cheerful suburban backyard, a wide green lawn across the foreground, a light wooden fence across the back, a big leafy tree on the left, a small veranda on the right, warm sunny afternoon sky"),
 ("bg_peppa", "a cheerful green grassy meadow with gentle rolling hills, three round brown muddy puddles spread across the foreground grass, a few small white and yellow flowers, bright blue sky with round fluffy white clouds"),
]

POST_TRANSPARENT = r"""
生成完每一张图后，必须做以下后处理（这一步不能省，直接生成的图是白底）：
  magick raw/<name>-src.png -alpha set -bordercolor white -border 1 -fuzz 14%% -fill none -floodfill +0+0 white -shave 1x1 raw/<name>.png
说明：必须用 floodfill 从角落泛洪抠图（只删除与边缘连通的白色区域），
绝对不要用 -transparent white 或 -fuzz 全局替换，那会把角色身上的白色（眼白、牙齿、白衣服）也挖空、并在浅色区域留下麻点。
然后用 magick 验证四角 alpha=0：
  magick raw/<name>.png -format "<name>: %%wx%%h corners=%%[pixel:p{2,2}] %%[pixel:p{1021,2}] %%[pixel:p{2,1021}] %%[pixel:p{1021,1021}]\n" info:
把验证输出打印出来。若四角不是 srgba(...,0)，调大 fuzz 到 20%% 重做后处理；若仍失败则重新生成该图。
中间文件 raw/<name>-src.png 保留即可，不要删除。
"""

POST_OPAQUE = r"""
背景图不需要透明，直接保存为 raw/<name>.png 即可（不要做抠图）。
保存后用 magick 打印尺寸确认：
  magick raw/<name>.png -format "<name>: %%wx%%h\n" info:
"""


def emit(batch_id, items, style, post, size):
    lines = []
    lines.append("用 GPT Image 2 生成 %d 张图片，保存到项目的 raw/ 目录。" % len(items))
    lines.append("")
    lines.append("【统一美术风格】每一张图的提示词都必须在末尾完整拼接这一整段风格描述，一字不改，以保证所有素材风格完全一致：")
    lines.append("STYLE = \"%s\"" % style)
    lines.append("")
    lines.append("【尺寸】每张图 %s。" % size)
    lines.append("")
    lines.append("【要生成的图】")
    for i, (name, desc) in enumerate(items, 1):
        lines.append("%d) 文件名 raw/%s.png ——  提示词 = \"%s\" + STYLE" % (i, name, desc))
    lines.append("")
    lines.append(post.strip())
    lines.append("")
    lines.append("全部完成后，用一条 magick 命令一次性打印所有产出图的尺寸与四角像素作为最终验证汇总。")
    p = os.path.join(OUT, "b%02d.txt" % batch_id)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return p, [n for n, _ in items]


def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


manifest = []
bid = 0
for grp in chunk(CHARS, 3):
    bid += 1
    p, names = emit(bid, grp, STYLE, POST_TRANSPARENT, "1024x1024")
    manifest.append({"batch": bid, "file": p, "names": names, "kind": "char"})
for grp in chunk(PROPS, 3):
    bid += 1
    p, names = emit(bid, grp, STYLE, POST_TRANSPARENT, "1024x1024")
    manifest.append({"batch": bid, "file": p, "names": names, "kind": "prop"})
for grp in chunk(BGS, 2):
    bid += 1
    p, names = emit(bid, grp, BG_STYLE, POST_OPAQUE, "1536x1024 横版（若模型只支持正方形则用 1024x1024）")
    manifest.append({"batch": bid, "file": p, "names": names, "kind": "bg"})

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print("batches:", bid, "images:", len(CHARS) + len(PROPS) + len(BGS))
for m in manifest:
    print(m["batch"], m["kind"], ",".join(m["names"]))
