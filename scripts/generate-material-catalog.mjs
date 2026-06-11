import { readdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const materialsDir = path.join(root, 'public', 'materials')
const svgDir = path.join(materialsDir, 'svg')

const rawCatalog = `
1|眼镜橘猫|Glasses cat|animal|cat|猫,橘猫,眼镜|cute,pet|cute,playful|hero,sticker
2|灰色猫咪|Gray cat|animal|cat|猫,灰猫,宠物|cute,pet|cute,calm|hero,sticker
3|胡萝卜兔|Carrot rabbit|animal|rabbit|兔子,胡萝卜,蔬菜|cute,nature|cute,playful|hero,sticker
4|柠檬|Lemon|food|lemon|柠檬,水果,酸味|food,nature|fresh,cheerful|sticker,decoration
5|汉堡|Hamburger|food|burger|汉堡,快餐,食物|food|cheerful,playful|sticker,hero
6|绿色金字塔|Green pyramid|symbol|pyramid|金字塔,三角形,几何|abstract,geometry|calm,playful|sticker,decoration
7|仙人掌|Cactus|nature|cactus|仙人掌,植物,沙漠|nature,desert|playful,energetic|hero,sticker
8|蓝发男孩|Blue-haired boy|character|boy|男孩,蓝色头发,头像|people,cute|cute,calm|hero,sticker
9|彩色运动鞋|Colorful sneaker|fashion|sneaker|鞋子,运动鞋,潮流|fashion,sport|energetic,playful|sticker,hero
10|绿色袜子|Green sock|fashion|sock|袜子,绿色,服饰|fashion,cozy|calm,cozy|sticker,decoration
11|蓝色毛怪|Blue furry monster|character|monster|怪兽,蓝色,毛绒|monster,cute|energetic,funny|hero,sticker
12|黄色小鸡|Yellow chick|animal|chick|小鸡,鸟,黄色|cute,nature|cute,cheerful|hero,sticker
13|红色花朵|Red flower|nature|flower|花,红花,植物|nature,romance|cheerful,romantic|sticker,decoration
14|红色蝴蝶结|Red bow|fashion|bow|蝴蝶结,礼物,装饰|fashion,romance|cute,romantic|sticker,decoration
15|蓝色小鸟|Blue bird|animal|bird|小鸟,蓝鸟,鸟|cute,nature|cute,calm|hero,sticker
16|熊猫幽灵|Panda ghost|fantasy|panda-ghost|熊猫,幽灵,万圣节|fantasy,holiday|funny,mysterious|hero,sticker
17|绿色恐龙|Green dinosaur|animal|dinosaur|恐龙,绿色,史前动物|dinosaur,cute|energetic,funny|hero,sticker
18|红色蘑菇|Red mushroom|nature|mushroom|蘑菇,植物,森林|nature,fantasy|cute,mysterious|sticker,hero
19|咆哮棕熊|Roaring bear|animal|bear|熊,棕熊,咆哮|animal,adventure|energetic,funny|hero,sticker
20|蓝色史莱姆|Blue slime|character|slime|史莱姆,水滴,蓝色|monster,fantasy|calm,cute|hero,sticker
21|微笑太阳|Smiling sun|nature|sun|太阳,阳光,天气|weather,nature|cheerful,energetic|sticker,decoration
22|棕色小狗|Brown dog|animal|dog|狗,小狗,宠物|pet,cute|cute,playful|hero,sticker
23|牛角毛怪|Horned furry monster|character|horned-monster|怪兽,牛角,棕色|monster,fantasy|mysterious,funny|hero,sticker
24|脑花纸杯蛋糕|Brain cupcake|food|cupcake|纸杯蛋糕,甜品,脑花|food,funny|funny,cute|sticker,hero
25|橘色狐狸|Orange fox|animal|fox|狐狸,橘色,森林动物|nature,cute|cute,calm|hero,sticker
26|黄色礼物盒|Yellow gift box|object|gift-box|礼物,礼盒,蝴蝶结|holiday,celebration|cute,cheerful|sticker,decoration
27|手持镜子|Hand mirror|object|mirror|镜子,梳妆,蝴蝶结|fashion,daily|cute,calm|sticker,decoration
28|白色雪怪|White yeti|character|yeti|雪怪,白色,冬天|winter,fantasy|cute,funny|hero,sticker
29|绿色墨西哥卷|Green taco|food|taco|卷饼,墨西哥卷,食物|food|cheerful,playful|sticker,hero
30|电子琴|Keyboard synthesizer|music|keyboard|电子琴,键盘,乐器|music,retro|energetic,creative|sticker,hero
31|绿色青蛙|Green frog|animal|frog|青蛙,绿色,两栖动物|nature,cute|playful,funny|hero,sticker
32|咧嘴棕熊|Grinning bear|animal|bear|熊,笑脸,棕熊|animal,cute|funny,cheerful|hero,sticker
33|蓝色鹿角怪|Blue antler monster|character|antler-monster|怪兽,鹿角,蓝色|monster,winter|cute,funny|hero,sticker
34|卡通火箭|Cartoon rocket|space|rocket|火箭,太空,宇宙,发射|space,technology,adventure|energetic,playful|hero,sticker
35|雪人|Snowman|character|snowman|雪人,冬天,圣诞|winter,holiday|cheerful,cozy|hero,sticker
36|独角鲸|Narwhal|animal|narwhal|独角鲸,鲸鱼,海洋|ocean,fantasy|cute,calm|hero,sticker
37|雷雨云|Thunder cloud|nature|thunder-cloud|乌云,闪电,雷雨|weather,nature|energetic,mysterious|sticker,decoration
38|橙色章鱼|Orange octopus|animal|octopus|章鱼,海洋,橙色|ocean,cute|cute,calm|hero,sticker
39|橙发美人鱼|Orange-haired mermaid|character|mermaid|美人鱼,女孩,海洋|ocean,fantasy|cute,playful|hero,sticker
41|耳机女孩|Headphone girl|character|girl|女孩,耳机,音乐|music,people|calm,cute|hero,sticker
42|黄色椭圆角色|Yellow oval character|character|oval-character|黄色角色,笑脸,牙齿|cute,funny|cheerful,funny|hero,sticker
43|坐姿狐狸|Sitting fox|animal|fox|狐狸,坐姿,橘色|nature,cute|calm,cute|hero,sticker
44|橙色宇航员|Orange astronaut|space|astronaut|宇航员,太空服,宇宙|space,technology,adventure|cute,calm|hero,sticker
45|蓝色书本|Blue book|stationery|book|书,阅读,书签|school,knowledge|calm,creative|sticker,icon
46|爱心咖啡杯|Heart coffee cup|food|coffee|咖啡,纸杯,爱心|food,cozy,romance|cozy,romantic|sticker,icon
47|鱼骨|Fish skeleton|symbol|fish-bone|鱼骨,骨头,海洋|ocean,funny|funny,mysterious|sticker,decoration
48|黑胶唱片|Vinyl record|music|vinyl-record|唱片,黑胶,音乐|music,retro|energetic,nostalgic|sticker,icon
49|绿色长腿角色|Green long-legged character|character|green-character|绿色角色,长腿,闭眼|cute,calm|calm,cute|hero,sticker
50|牛奶瓶|Milk bottle|food|milk|牛奶,瓶子,饮料|food,daily|fresh,calm|sticker,icon
51|喷漆罐|Spray paint can|stationery|spray-can|喷漆,涂鸦,创作|art,urban|creative,energetic|sticker,icon
52|长翅膀笑脸|Winged smiley|symbol|winged-smiley|笑脸,翅膀,飞行|cute,fantasy|cheerful,playful|sticker,decoration
53|绿色方块角色|Green block character|character|block-character|方块角色,绿色,长腿|cute,geometry|cute,calm|hero,sticker
54|芝麻汉堡|Sesame burger|food|burger|汉堡,芝麻,快餐|food|cheerful,playful|sticker,hero
55|红黄旋涡|Red yellow swirl|symbol|swirl|旋涡,红色,黄色|abstract,retro|energetic,playful|sticker,decoration
56|灰色音箱|Gray speaker|music|speaker|音箱,扬声器,音乐|music,technology|energetic,retro|sticker,icon
57|外星飞碟|Alien UFO|space|ufo|外星人,飞碟,UFO|space,technology|cute,mysterious|hero,sticker
58|橙色彗星|Orange comet|space|comet|彗星,流星,橙色|space,adventure|energetic,playful|sticker,decoration
59|音箱机器人|Speaker robot|music|speaker-robot|音箱,机器人,音乐|music,technology|energetic,funny|hero,sticker
60|蓝色长耳怪|Blue long-eared monster|character|long-ear-monster|怪兽,蓝色,长耳朵|monster,cute|funny,playful|hero,sticker
61|点赞拍立得|Thumbs-up photo|technology|instant-photo|照片,点赞,拍立得|social,technology|cheerful,playful|sticker,icon
62|刺猬|Hedgehog|animal|hedgehog|刺猬,动物,灰色|nature,cute|calm,cute|hero,sticker
63|弯曲钢琴|Curved piano|music|piano|钢琴,键盘,乐器|music,creative|creative,playful|sticker,decoration
64|绿色史莱姆|Green slime|character|slime|史莱姆,绿色,黏液|monster,fantasy|funny,mysterious|hero,sticker
65|绿色小恐龙|Green little dinosaur|animal|dinosaur|恐龙,绿色,怪兽|dinosaur,cute|playful,funny|hero,sticker
66|红绿冰棒|Red green popsicle|food|popsicle|冰棒,冰淇淋,甜品|food,summer|fresh,cheerful|sticker,hero
67|蓝色太空肉排|Blue space drumstick|food|space-drumstick|肉排,骨头,蓝色|food,space,funny|funny,mysterious|sticker,hero
68|黄色铅笔|Yellow pencil|stationery|pencil|铅笔,文具,绘画|school,art|creative,calm|sticker,icon
69|黄色独眼球怪|Yellow cyclops ball|character|cyclops|独眼怪,黄色,圆形|monster,cute|funny,energetic|hero,sticker
70|黄色毛怪|Yellow furry monster|character|furry-monster|怪兽,黄色,毛绒|monster,cute|funny,playful|hero,sticker
71|画笔|Paint brush|stationery|paint-brush|画笔,绘画,艺术|art,school|creative,calm|sticker,icon
72|游泳圈橘猫|Cat in swim ring|animal|cat|猫,游泳圈,橘猫|summer,pet|cute,relaxed|hero,sticker
73|橙色布偶怪|Orange stitched monster|character|stitched-monster|怪兽,布偶,橙色|monster,handmade|funny,cute|hero,sticker
74|眼球植物|Eyeball plant|fantasy|eyeball-plant|眼球,植物,怪异|fantasy,monster|mysterious,funny|hero,sticker
75|蓝白条纹角色|Blue striped character|character|striped-character|条纹角色,蓝色,白色|cute,abstract|cute,calm|hero,sticker
76|棕色小狗|Brown puppy|animal|dog|狗,小狗,宠物|pet,cute|cute,playful|hero,sticker
77|蓝色幽灵|Blue ghost|fantasy|ghost|幽灵,蓝色,鬼怪|fantasy,holiday|cute,playful|hero,sticker
78|奶牛|Cow|animal|cow|奶牛,农场,动物|farm,nature|cute,calm|hero,sticker
79|绿发男孩|Green-haired boy|character|boy|男孩,绿色头发,头像|people,cute|cheerful,cute|hero,sticker
80|吐舌独眼怪|Tongue cyclops|character|cyclops|独眼怪,舌头,蓝色|monster,funny|funny,energetic|hero,sticker
81|圣诞袜角色|Christmas stocking character|character|stocking-character|圣诞袜,冬天,角色|winter,holiday|cute,cheerful|hero,sticker
82|蓝色独眼怪|Blue cyclops|character|cyclops|独眼怪,蓝色,怪兽|monster,cute|funny,playful|hero,sticker
83|蓝色机器人|Blue robot|technology|robot|机器人,天线,科技|technology,cute|cheerful,playful|hero,sticker
84|骷髅头|Skull|symbol|skull|骷髅,骨头,万圣节|holiday,fantasy|mysterious,funny|sticker,icon
85|粉色甜甜圈|Pink donut|food|donut|甜甜圈,甜品,粉色|food,cute|cute,cheerful|sticker,hero
86|旋涡棒棒糖|Swirl lollipop|food|lollipop|棒棒糖,糖果,甜品|food,cute|cheerful,playful|sticker,decoration
87|老虎棒棒糖|Tiger lollipop|food|lollipop|棒棒糖,老虎,糖果|food,cute|cute,playful|sticker,decoration
88|花朵棒棒糖|Flower lollipop|food|lollipop|棒棒糖,花朵,糖果|food,nature|cheerful,playful|sticker,decoration
89|红色嘴唇|Red lips|face-part|lips|嘴唇,红唇,表情|romance,funny|funny,romantic|facePart,sticker
90|纸飞机|Paper airplane|symbol|paper-airplane|纸飞机,飞行,折纸|adventure,school|calm,playful|sticker,decoration
91|黄色星球|Yellow planet|space|planet|星球,月球,宇宙|space,adventure|mysterious,playful|hero,sticker
92|冬帽蓝色角色|Winter blue character|character|winter-character|冬帽,蓝色角色,冬天|winter,cute|cute,cozy|hero,sticker
93|升空火箭|Launching rocket|space|rocket|火箭,升空,烟雾|space,technology,adventure|energetic,cheerful|hero,sticker
94|WTF 对话框|WTF speech bubble|callout|text-callout|WTF,对话框,文字|social,funny|funny,energetic|callout,sticker
95|墨镜香蕉|Sunglasses banana|food|banana|香蕉,墨镜,水果|food,summer,funny|funny,cheerful|hero,sticker
96|红色马克笔|Red marker|stationery|marker|马克笔,画笔,文具|art,school|creative,energetic|sticker,icon
97|吹萨克斯的蓝熊|Blue bear with saxophone|music|saxophone-bear|熊,萨克斯,音乐|music,cute|creative,calm|hero,sticker
99|长尾灰猫|Long-tail gray cat|animal|cat|猫,灰猫,长尾巴|pet,cute|calm,cute|hero,sticker
100|棕色松鼠|Brown squirrel|animal|squirrel|松鼠,尾巴,森林动物|nature,cute|cute,playful|hero,sticker
101|棕色牛角怪|Brown horned monster|character|horned-monster|怪兽,牛角,棕色|monster,fantasy|funny,playful|hero,sticker
102|绿色独眼毛球|Green eyeball monster|character|eyeball-monster|独眼怪,毛球,绿色|monster,fantasy|mysterious,funny|hero,sticker
103|切片菠萝|Sliced pineapple|food|pineapple|菠萝,水果,切片|food,summer|fresh,playful|sticker,hero
104|棕熊头像|Brown bear head|animal|bear|熊,头像,棕色|animal,cute|calm,cute|hero,sticker
105|灰色触控笔|Gray stylus|technology|stylus|触控笔,数位笔,科技|technology,art|creative,calm|sticker,icon
106|绿色折叠纸|Green folded paper|object|folded-paper|纸张,折叠,绿色|school,abstract|calm,creative|sticker,decoration
107|摇滚手势|Rock hand gesture|symbol|hand-gesture|手势,摇滚,手掌|music,funny|energetic,playful|sticker,icon
108|篝火|Campfire|nature|campfire|篝火,火焰,木柴|nature,adventure|cozy,energetic|sticker,hero
109|复古手机|Retro mobile phone|technology|mobile-phone|手机,按键,复古|technology,retro|calm,nostalgic|sticker,icon
110|复古电视|Retro television|technology|television|电视,复古,屏幕|technology,retro|cheerful,nostalgic|sticker,hero
112|睡觉的棕猫|Sleeping brown cat|animal|cat|猫,睡觉,宠物|pet,cozy|calm,cozy|hero,sticker
113|茶包|Tea bag|food|tea-bag|茶包,茶叶,饮品|food,cozy|calm,cozy|sticker,icon
114|紫色水母|Purple jellyfish|animal|jellyfish|水母,海洋,紫色|ocean,fantasy|calm,mysterious|hero,sticker
115|浣熊|Raccoon|animal|raccoon|浣熊,森林动物,灰色|nature,cute|calm,cute|hero,sticker
116|蓝色冰棒|Blue popsicle|food|popsicle|冰棒,蓝色,甜品|food,summer|fresh,playful|sticker,hero
117|爱心棒棒糖|Heart lollipop|food|lollipop|棒棒糖,爱心,糖果|food,romance|romantic,cute|sticker,decoration
118|菠萝|Pineapple|food|pineapple|菠萝,水果,热带|food,summer|fresh,cheerful|sticker,hero
119|星星对话框|Star speech bubble|callout|star-callout|星星,对话框,绿色|social,cute|cheerful,playful|callout,sticker
120|披萨|Pizza slice|food|pizza|披萨,芝士,快餐|food|cheerful,playful|sticker,hero
122|微笑云朵|Smiling cloud|nature|cloud|云朵,天气,蓝色|weather,nature|cheerful,calm|sticker,decoration
123|樱桃纸杯蛋糕|Cherry cupcake|food|cupcake|纸杯蛋糕,樱桃,甜品|food,cute|cute,cheerful|sticker,hero
124|彩虹|Rainbow|nature|rainbow|彩虹,云朵,天气|weather,nature|cheerful,hopeful|sticker,decoration
125|蓝色钻石|Blue diamond|symbol|diamond|钻石,宝石,蓝色|luxury,geometry|mysterious,elegant|sticker,decoration
126|绿色右箭头|Green right arrow|symbol|arrow|箭头,方向,绿色|navigation,abstract|energetic,playful|icon,decoration
128|绿色旋涡|Green swirl|symbol|swirl|旋涡,绿色,波浪|abstract,nature|calm,playful|sticker,decoration
129|绿色波浪|Green wave|nature|wave|波浪,绿色,旋涡|nature,ocean,abstract|calm,energetic|sticker,decoration
130|樱桃|Cherries|food|cherry|樱桃,水果,红色|food,nature|fresh,romantic|sticker,decoration
131|黄色信封|Yellow envelope|object|envelope|信封,邮件,消息|communication,social|calm,cheerful|sticker,icon
132|西瓜|Watermelon slice|food|watermelon|西瓜,水果,夏天|food,summer|fresh,cheerful|sticker,hero
133|彩色棒棒糖|Colorful lollipop|food|lollipop|棒棒糖,糖果,彩色|food,cute|cheerful,playful|sticker,decoration
134|爆米花|Popcorn|food|popcorn|爆米花,电影,零食|food,entertainment|cheerful,cozy|sticker,hero
135|蓝色方形角色|Blue square character|character|blue-character|蓝色角色,方形,微笑|cute,abstract|cute,calm|hero,sticker
136|仙人掌盆栽|Cactus cluster|nature|cactus|仙人掌,植物,沙漠|nature,desert|fresh,playful|hero,sticker
137|黄色流星|Yellow shooting star|space|shooting-star|流星,星星,彗星|space,adventure|energetic,hopeful|sticker,decoration
138|爱心点赞气泡|Heart notification bubble|callout|notification|爱心,点赞,通知,数字1|social,romance|cheerful,romantic|callout,icon
139|蓝色向下箭头|Blue down arrow|symbol|arrow|箭头,向下,蓝色|navigation,technology|energetic,playful|icon,decoration
140|蓝色宝石|Blue gemstone|symbol|gemstone|宝石,水晶,蓝色|luxury,fantasy|mysterious,elegant|sticker,decoration
141|牛角面包|Croissant|food|croissant|牛角包,面包,早餐|food,cozy|cozy,cheerful|sticker,hero
142|和平标志|Peace sign|symbol|peace-sign|和平,标志,圆形|social,retro|calm,hopeful|sticker,icon
143|粉色爱心|Pink heart|symbol|heart|爱心,粉色,爱情|romance,cute|romantic,cute|sticker,decoration
144|张嘴表情|Open mouth|face-part|mouth|嘴巴,牙齿,表情|funny,monster|funny,energetic|facePart,sticker
146|吐舌嘴巴|Tongue mouth|face-part|mouth|嘴巴,舌头,牙齿|funny,monster|funny,playful|facePart,sticker
147|牙齿笑线|Teeth smile line|face-part|teeth|牙齿,微笑,表情|funny,cute|funny,cheerful|facePart,decoration
148|伸舌表情部件|Tongue face part|face-part|tongue|舌头,嘴巴,表情|funny,monster|funny,playful|facePart,decoration
150|圆角对话框|Rounded speech bubble|callout|speech-bubble|对话框,气泡,空白|communication,social|calm,playful|callout
152|云形对话框|Cloud speech bubble|callout|speech-bubble|云朵,对话框,空白|communication,cute|calm,cute|callout
153|花边气泡|Scalloped bubble|callout|speech-bubble|气泡,花边,空白|communication,cute|cute,playful|callout
154|方形对话框|Square speech bubble|callout|speech-bubble|对话框,方形,空白|communication,social|calm,playful|callout
155|思考气泡|Thought bubble|callout|thought-bubble|思考,气泡,空白|communication,cute|calm,playful|callout
156|爆炸气泡|Burst bubble|callout|burst-bubble|爆炸框,强调,空白|communication,comic|energetic,playful|callout
157|竖向对话框|Vertical speech bubble|callout|speech-bubble|对话框,竖向,空白|communication,social|calm,playful|callout
159|椭圆对话框|Oval speech bubble|callout|speech-bubble|对话框,椭圆,空白|communication,social|calm,playful|callout
160|漫画爆炸框|Comic burst bubble|callout|burst-bubble|漫画,爆炸框,强调|communication,comic|energetic,playful|callout
`.trim()

const colorAliases = new Map([
  ['#231F20', 'black'],
  ['#BE1E2D', 'red'],
  ['#EF4136', 'red'],
  ['#E27683', 'pink'],
  ['#F7941E', 'orange'],
  ['#FBB040', 'orange'],
  ['#F2B879', 'tan'],
  ['#FFF200', 'yellow'],
  ['#8DC63F', 'green'],
  ['#009444', 'green'],
  ['#009344', 'green'],
  ['#00AEEF', 'blue'],
  ['#88E0FF', 'light-blue'],
  ['#27AAE1', 'blue'],
  ['#2E3192', 'indigo'],
  ['#2B3990', 'indigo'],
  ['#662D91', 'purple'],
  ['#754C29', 'brown'],
  ['#A97C50', 'brown'],
  ['#603913', 'brown'],
  ['#8B5E3C', 'brown'],
  ['#939598', 'gray'],
  ['#58595B', 'gray'],
  ['#414042', 'gray'],
  ['#FFFFFF', 'white'],
])

function parseRows() {
  return new Map(
    rawCatalog.split('\n').map((line) => {
      const [number, zh, en, category, subject, keywords, themes, moods, roles] = line.split('|')
      return [
        Number(number),
        {
          zh,
          en,
          category,
          subjects: [subject],
          keywords: keywords.split(','),
          themes: themes.split(','),
          moods: moods.split(','),
          roles: roles.split(','),
        },
      ]
    }),
  )
}

function extractColors(svg) {
  const hexValues = [...svg.matchAll(/#[0-9a-f]{6}\b/gi)].map((match) => match[0].toUpperCase())
  const colors = [...new Set(hexValues.map((hex) => colorAliases.get(hex)).filter(Boolean))]
  return colors.length ? colors : ['multicolor']
}

function countPaths(svg) {
  return (svg.match(/<path\b/g) || []).length
}

function recommendedPositions(roles) {
  if (roles.includes('callout')) return ['top', 'center']
  if (roles.includes('facePart')) return ['center']
  if (roles.includes('icon')) return ['top-left', 'top-right', 'bottom-left', 'bottom-right']
  if (roles.includes('hero')) return ['center', 'bottom-center']
  return ['top-right', 'bottom-left', 'bottom-right']
}

function visualWeight(pathCount) {
  if (pathCount <= 8) return 'light'
  if (pathCount <= 30) return 'medium'
  return 'heavy'
}

const metadata = parseRows()
const svgFiles = (await readdir(svgDir)).filter((file) => file.endsWith('.svg')).sort()
const assets = []

for (const file of svgFiles) {
  const match = file.match(/doodle-(\d+)\.svg$/)
  if (!match) throw new Error(`Unexpected SVG filename: ${file}`)

  const number = Number(match[1])
  const manual = metadata.get(number)
  if (!manual) throw new Error(`Missing curated metadata for ${file}`)

  const svg = await readFile(path.join(svgDir, file), 'utf8')
  const pathCount = countPaths(svg)
  assets.push({
    assetId: `doodle-${String(number).padStart(3, '0')}`,
    file,
    src: `/materials/svg/${file}`,
    name: { zh: manual.zh, en: manual.en },
    description: `粗黑描边的${manual.zh}扁平卡通贴纸，色彩明亮，透明背景，适合作为锁屏装饰元素。`,
    category: manual.category,
    subjects: manual.subjects,
    keywords: [...new Set([...manual.keywords, manual.zh, manual.en.toLowerCase()])],
    themes: manual.themes,
    moods: manual.moods,
    roles: manual.roles,
    colors: extractColors(svg),
    recommendedPositions: recommendedPositions(manual.roles),
    visualWeight: visualWeight(pathCount),
    style: ['cartoon', 'doodle', 'bold-outline', 'flat-color'],
    width: 600,
    height: 600,
    viewBox: '0 0 600 600',
    transparent: true,
    recolorable: true,
    containsText: number === 94 || number === 138,
    pathCount,
  })
}

if (assets.length !== metadata.size) {
  throw new Error(`Catalog rows (${metadata.size}) do not match SVG files (${assets.length})`)
}

await writeFile(path.join(materialsDir, 'assets.json'), `${JSON.stringify(assets, null, 2)}\n`, 'utf8')
console.log(`Generated ${assets.length} material records.`)
