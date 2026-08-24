// api/postService.js - 添加缓存机制和按ID获取帖子
// 缓存变量
let cachedPosts = null;

// 生成 mock 数据（如果已有缓存则返回缓存）
export const generateMockPosts = (forceRefresh = false) => {
  if (cachedPosts && !forceRefresh) {
    return cachedPosts;
  }

  const posts = [];

  const categories = ["高危案例", "防骗技巧", "AI反诈专题"];
  const riskTexts = {
    高危案例: "高危预警",
    防骗技巧: "防骗技巧",
    AI反诈专题: "AI专题",
  };

  const tagsMap = {
    高危案例: ["#AI诈骗", "#冒充公检法", "#刷单诈骗", "#杀猪盘", "#虚假投资"],
    防骗技巧: ["#识别技巧", "#防范指南", "#转账必看", "#核实方法", "#安全设置"],
    AI反诈专题: [
      "#AI换脸",
      "#语音合成",
      "#深度伪造",
      "#AI诈骗识别",
      "#技术科普",
    ],
  };

  // 头像图片池
  const avatars = [
    "https://picsum.photos/id/63/100/100",
    "https://picsum.photos/id/65/100/100",
    "https://picsum.photos/id/66/100/100",
    "https://picsum.photos/id/67/100/100",
    "https://picsum.photos/id/68/100/100",
    "https://picsum.photos/id/69/100/100",
    "https://picsum.photos/id/70/100/100",
    "https://picsum.photos/id/71/100/100",
    "https://picsum.photos/id/72/100/100",
    "https://picsum.photos/id/73/100/100",
  ];

  // 帖子配图池
  const postImages = [
    "https://picsum.photos/id/0/400/300",
    "https://picsum.photos/id/1/400/300",
    "https://picsum.photos/id/2/400/300",
    "https://picsum.photos/id/3/400/300",
    "https://picsum.photos/id/4/400/300",
    "https://picsum.photos/id/5/400/300",
    "https://picsum.photos/id/6/400/300",
    "https://picsum.photos/id/7/400/300",
    "https://picsum.photos/id/8/400/300",
    "https://picsum.photos/id/9/400/300",
    "https://picsum.photos/id/10/400/300",
    "https://picsum.photos/id/11/400/300",
    "https://picsum.photos/id/12/400/300",
    "https://picsum.photos/id/13/400/300",
    "https://picsum.photos/id/14/400/300",
    "https://picsum.photos/id/15/400/300",
    "https://picsum.photos/id/16/400/300",
    "https://picsum.photos/id/17/400/300",
    "https://picsum.photos/id/18/400/300",
    "https://picsum.photos/id/19/400/300",
  ];

  // 多图帖子配图池
  const multiImagesMap = {
    高危案例: [
      "https://picsum.photos/id/20/400/300",
      "https://picsum.photos/id/21/400/300",
      "https://picsum.photos/id/22/400/300",
    ],
    防骗技巧: [
      "https://picsum.photos/id/23/400/300",
      "https://picsum.photos/id/24/400/300",
      "https://picsum.photos/id/25/400/300",
    ],
    AI反诈专题: [
      "https://picsum.photos/id/26/400/300",
      "https://picsum.photos/id/27/400/300",
      "https://picsum.photos/id/28/400/300",
    ],
  };

  const usernames = [
    "反诈小卫士",
    "小明同学",
    "李阿姨",
    "程序员老王",
    "大学生小张",
    "退休教师",
    "宝妈欣欣",
    "职场小白",
    "金融从业者",
    "热心市民",
    "网络安全专家",
    "反诈志愿者",
    "社区民警",
    "信息安全师",
    "法律顾问",
  ];

  // 当前用户昵称（与 Community.jsx 保持一致）
  const currentUserNickname = "verbea";

  const titles = {
    高危案例: [
      "AI换脸冒充熟人借钱，我差点被骗5万",
      '接到"社保局"电话说卡异常，是诈骗吗？',
      "刷单返利骗局揭秘：我如何被骗了3万",
      "虚假投资理财平台曝光，大家警惕！",
      "冒充客服退款诈骗，差点点进钓鱼链接",
      "杀猪盘套路：网恋对象带我投资",
      '收到"银行"短信说账户异常，千万别点',
      "AI语音合成冒充领导要求转账",
    ],
    防骗技巧: [
      "如何识别AI换脸视频？这5招教你",
      "转账前必看：反诈中心紧急提醒",
      "虚假贷款平台套路全解析",
      "96110来电一定要接！反诈中心提醒",
      "防骗小技巧：转账前多做这三件事",
      "如何辨别真假警察？记住这几点",
      "收到陌生链接怎么办？正确做法",
      "家人被骗了怎么办？紧急处理指南",
    ],
    AI反诈专题: [
      "AI换脸诈骗识别指南",
      "语音合成诈骗防范技巧",
      "深度伪造技术揭秘：如何识破",
      "AI诈骗最新套路全解析",
      "当AI学会骗人，我们该怎么办",
      "AI反诈技术原理科普",
      "如何保护你的生物特征信息",
      "AI时代的新型诈骗防范",
    ],
  };

  const contents = {
    高危案例: [
      '昨晚接到"表哥"视频通话，脸和声音都一模一样，说急用钱让转账。幸好我多问了一句私事，对方露馅了。后来核实表哥根本没找我。AI诈骗太逼真了，大家一定要设置转账暗号！\n\n对方还发来了身份证照片，看起来也很真实。现在想想都是AI生成的。这种诈骗手段太可怕了，大家一定要提高警惕！',
      "刚接到自称社保局的电话，说我的社保卡异常，让我按9转人工。我挂了电话，但有点担心是不是真的？社保局会这样打电话吗？\n\n电话里说我的社保卡在外地有异常消费，需要立即处理，否则会被冻结。我一开始有点慌，但想到之前看过的反诈宣传，还是先挂了电话。",
      "看到朋友圈有人发刷单兼职，一单佣金50，我试了第一单真的返钱了。然后他说要连做5单才能提现，我转了3万后就被拉黑了。千万不要信刷单！\n\n后来我在网上搜索，发现很多人都有类似经历。骗子先给小额返利获取信任，然后诱导大额投入后消失。",
      "网友推荐了一个投资平台，说稳赚不赔，我投了1万确实赚了2000。然后他说要升级会员才能提现大额，我充了5万后平台就登不上了。\n\n这种杀猪盘套路太深了，他们甚至还会安排所谓的老师指导操作，让你感觉真的很专业。",
      "接到自称淘宝客服电话，说我买的商品有质量问题要退款，让我点链接填写银行卡信息。还好我多看了一眼网址，是钓鱼网站！\n\n正规退款应该原路返回，不需要提供任何银行卡信息。大家一定要记住这一点！",
      "在交友软件认识了一个女生，聊得很投缘，她说她懂投资想带我一起赚钱。我投了2万后她就消失了，后来才知道是杀猪盘。\n\n现在想想很多细节都很可疑，但当时被感情蒙蔽了双眼。交友需谨慎，涉及金钱更要警惕。",
      "收到95588的短信说账户异常需要验证，链接看着很正规。差点就点了，还好我先打了客服电话确认，是诈骗短信。\n\n千万不要点击短信中的链接，应该自己拨打官方客服电话核实。",
      '接到"总经理"电话，声音一模一样，说急需用钱让我转账。我正准备转，同事提醒说总经理在开会，才发现是AI合成的。\n\n现在的AI技术太发达了，连声音都能完美模仿。以后遇到紧急转账一定要当面或视频确认。',
    ],
    防骗技巧: [
      "AI换脸视频识别技巧：\n1. 让对方做特定动作（比如摸鼻子、转头）\n2. 询问只有你们知道的私事\n3. 注意视频边缘是否模糊\n4. 观察眨眼频率是否自然\n5. 用语音通话再次确认\n\n记住：眼见不一定为实！",
      "转账前必做三件事：\n1. 电话语音确认\n2. 询问只有对方知道的私密信息\n3. 等待30分钟冷静期\n\n记住：任何紧急转账都值得再确认一次！",
      "虚假贷款平台特征：\n1. 要求先交保证金\n2. 利率异常低\n3. 无需审核\n4. 客服态度异常好\n5. 要求下载不明APP\n\n遇到这些直接拉黑！",
      "96110是反诈中心专用号码，接到一定要接！这不是诈骗电话，是预警电话。如果你接到96110，说明你可能正在遭遇诈骗。\n\n请务必接听并配合民警的提醒！",
      "防骗小技巧：\n1. 设置转账延迟到账\n2. 和家人约定转账暗号\n3. 不要轻易分享验证码\n4. 定期清理手机垃圾短信\n5. 安装国家反诈中心APP",
      "如何辨别真假警察：\n1. 真警察不会要求转账\n2. 不会电话做笔录\n3. 不会要求下载不明软件\n4. 可以直接打110核实\n\n任何要求转账的都是骗子！",
      "收到陌生链接的正确做法：\n1. 不要点！\n2. 复制链接到浏览器查看域名\n3. 用反诈APP检测\n4. 直接删除\n5. 举报到12321",
      "家人被骗了怎么办：\n1. 立即停止转账\n2. 保存所有证据\n3. 拨打96110咨询\n4. 报警处理\n5. 安抚家人情绪\n\n时间越早，追回可能性越大！",
    ],
    AI反诈专题: [
      "AI换脸诈骗识别指南：\n\n• 注意视频中面部边缘是否自然\n• 眨眼频率是否正常\n• 声音是否与画面同步\n• 要求对方做特定动作\n• 问只有你们知道的私密问题\n\n科技发展带来便利也带来风险，请提高警惕！",
      "语音合成诈骗防范：\n\n• 要求对方说出只有你们知道的信息\n• 注意语气是否自然\n• 挂断后回拨确认\n• AI合成的声音在情绪表达上可能不够自然\n• 设置转账语音验证码",
      "深度伪造技术揭秘：\n\nDeepfake技术通过AI生成逼真的假视频，普通人难以辨别。防护方法：\n1. 多渠道核实\n2. 视频通话时让对方做特定动作\n3. 保护好自己的照片和声音\n4. 开启双重验证",
      "AI诈骗最新套路：\n1. AI换脸冒充亲友\n2. 语音合成冒充领导\n3. AI生成虚假新闻\n4. 智能客服诈骗\n5. 深度伪造视频诈骗\n\n了解套路，避免上当！",
      "当AI学会骗人，我们需要：\n1. 提高警惕\n2. 建立多层验证机制\n3. 保护个人生物特征\n4. 学习识别技巧\n5. 安装反诈软件\n\n技术永远是一把双刃剑。",
      "AI反诈技术原理：\n\n通过分析语音特征、面部微表情、语义模式等，AI可以识别出诈骗意图。系统会实时分析并给出预警。科技反诈，守护安全！",
      "如何保护生物特征：\n1. 不随意分享人脸照片\n2. 不在不可信平台录语音\n3. 使用虚拟形象\n4. 定期更换密码\n5. 开启双重验证\n\n生物特征是唯一的，保护好它！",
      "AI时代防范指南：\n1. 对陌生来电保持警惕\n2. 视频通话多加核实\n3. 不轻易转账\n4. 安装反诈APP\n5. 学习最新反诈知识\n\n与时俱进，防范新型诈骗！",
    ],
  };

  // 评论池
  const commentPool = [
    {
      id: 101,
      author: {
        nickname: "反诈小卫士",
        avatar: "https://picsum.photos/id/1/100/100",
        badge: "反诈先锋",
      },
      content: "这个案例太典型了，大家一定要提高警惕！",
      time: "1小时前",
      likes: 12,
    },
    {
      id: 102,
      author: {
        nickname: "小明同学",
        avatar: "https://picsum.photos/id/2/100/100",
        badge: null,
      },
      content: "感谢分享，学到了",
      time: "30分钟前",
      likes: 5,
    },
    {
      id: 103,
      author: {
        nickname: "李阿姨",
        avatar: "https://picsum.photos/id/3/100/100",
        badge: null,
      },
      content: "我也遇到过类似情况，直接挂了",
      time: "2小时前",
      likes: 8,
    },
    {
      id: 104,
      author: {
        nickname: "程序员老王",
        avatar: "https://picsum.photos/id/4/100/100",
        badge: "技术达人",
      },
      content: "这个技术分析很到位，点赞！",
      time: "5小时前",
      likes: 15,
    },
    {
      id: 105,
      author: {
        nickname: "大学生小张",
        avatar: "https://picsum.photos/id/5/100/100",
        badge: null,
      },
      content: "收藏了，转发给家人看看",
      time: "3小时前",
      likes: 6,
    },
    {
      id: 106,
      author: {
        nickname: "热心网友",
        avatar: "https://picsum.photos/id/6/100/100",
        badge: null,
      },
      content: "说得对！支持！",
      time: "30分钟前",
      likes: 3,
    },
  ];

  let id = 1;
  for (const category of categories) {
    const categoryTitles = titles[category];
    const categoryContents = contents[category];

    for (let i = 0; i < categoryTitles.length; i++) {
      const categoryTags = tagsMap[category];
      const randomTags = [...categoryTags]
        .sort(() => 0.5 - Math.random())
        .slice(0, Math.floor(Math.random() * 3) + 1);

      const daysAgo = Math.floor(Math.random() * 30);
      const hoursAgo = Math.floor(Math.random() * 24);
      const publishTime = daysAgo > 0 ? `${daysAgo}天前` : `${hoursAgo}小时前`;

      // 随机决定是否有图片（70%概率有图）
      const hasImage = Math.random() > 0.55;
      const images = hasImage
        ? [postImages[Math.floor(Math.random() * postImages.length)]]
        : [];

      // 随机生成1-3条评论
      const commentCount = Math.floor(Math.random() * 3) + 1;
      const comments = [];
      const usedComments = [...commentPool];
      for (let j = 0; j < commentCount && usedComments.length > 0; j++) {
        const randomIndex = Math.floor(Math.random() * usedComments.length);
        const commentTemplate = usedComments[randomIndex];
        usedComments.splice(randomIndex, 1);
        comments.push({
          ...commentTemplate,
          id: Date.now() + j + id * 100,
        });
      }

      // 为高危案例和AI专题添加多图
      let detailImages = images;
      if (category === "高危案例" || category === "AI反诈专题") {
        if (Math.random() > 0.7) {
          const multiImages = multiImagesMap[category];
          detailImages = [...multiImages];
        }
      }

      const isCurrentUser = Math.random() < 0.15;

      posts.push({
        id: id++,
        title: categoryTitles[i],
        content: categoryContents[i],
        author: {
          id: isCurrentUser ? 999 : Math.floor(Math.random() * 1000) + 1,
          nickname: isCurrentUser
            ? currentUserNickname
            : usernames[(id - 1) % usernames.length],
          avatar: isCurrentUser
            ? "/icons/10.png"
            : avatars[(id - 1) % avatars.length],
          badge: isCurrentUser
            ? null
            : Math.random() > 0.7
              ? category === "高危案例"
                ? "反诈先锋"
                : "认证用户"
              : null,
          isFollowed: false,
        },
        publishTime,
        tags: randomTags,
        category: category,
        likeCount: Math.floor(Math.random() * 80) + 10,
        commentCount: commentCount,
        isLiked: false,
        isSaved: false,
        riskLevel:
          category === "高危案例"
            ? "high"
            : category === "防骗技巧"
              ? "medium"
              : "low",
        riskText: riskTexts[category],
        comments: comments,
        images: images,
        detailImages: detailImages,
      });
    }
  }

  const sortedPosts = posts.sort((a, b) => {
    const getTimeValue = (timeStr) => {
      if (timeStr.includes("天")) return -parseInt(timeStr);
      if (timeStr.includes("小时")) return -parseInt(timeStr) / 24;
      return 0;
    };
    return getTimeValue(a.publishTime) - getTimeValue(b.publishTime);
  });

  // 存入缓存
  cachedPosts = sortedPosts;
  return sortedPosts;
};

// 根据 ID 获取单个帖子（使用缓存数据）
export const getPostById = (id) => {
  const allPosts = generateMockPosts();
  return allPosts.find((post) => post.id === parseInt(id));
};

// 获取当前用户的帖子（用于社区足迹的"我的帖子"）
export const getCurrentUserPosts = (currentUserNickname) => {
  const allPosts = generateMockPosts();
  return allPosts.filter(
    (post) => post.author.nickname === currentUserNickname,
  );
};

// 获取当前用户关注的用户（模拟）
export const getCurrentUserFollows = () => {
  return [
    {
      id: 1,
      name: "反诈民警老陈",
      avatar: "👮",
      bio: "反诈一线民警，分享真实案例",
      isOfficial: true,
      isFollowing: true,
    },
    {
      id: 2,
      name: "安全小助手",
      avatar: "🛡️",
      bio: "每日更新防骗小知识",
      isOfficial: false,
      isFollowing: true,
    },
    {
      id: 3,
      name: "李阿姨讲反诈",
      avatar: "👵",
      bio: "退休教师，义务宣传反诈知识",
      isOfficial: false,
      isFollowing: true,
    },
    {
      id: 4,
      name: "网络安全卫士",
      avatar: "💻",
      bio: "网络安全专家，专注AI诈骗防范",
      isOfficial: true,
      isFollowing: true,
    },
  ];
};

// 获取当前用户的粉丝（模拟）
export const getCurrentUserFans = () => {
  return [
    {
      id: 1,
      name: "小明同学",
      avatar: "👨",
      bio: "正在学习反诈知识",
      isOfficial: false,
      isFollowing: false,
      isMutual: false,
    },
    {
      id: 2,
      name: "王大姐",
      avatar: "👩",
      bio: "社区反诈志愿者",
      isOfficial: false,
      isFollowing: true,
      isMutual: true,
    },
    {
      id: 3,
      name: "张老师",
      avatar: "🧑‍🏫",
      bio: "退休教师，关注反诈",
      isOfficial: false,
      isFollowing: false,
      isMutual: false,
    },
    {
      id: 4,
      name: "小李",
      avatar: "🧑",
      bio: "大学生，分享防骗经历",
      isOfficial: false,
      isFollowing: true,
      isMutual: false,
    },
  ];
};

export const hotTopics = [
  { id: 1, title: "AI换脸/语音合成诈骗", 热度: "12.3w" },
  { id: 2, title: "刷单返利诈骗", 热度: "9.8w" },
  { id: 3, title: "虚假投资理财", 热度: "8.5w" },
  { id: 4, title: "如何辨别假公安", 热度: "6.2w" },
  { id: 5, title: "虚假贷款理财", 热度: "5.7w" },
  { id: 6, title: "冒充客服/京东金条", 热度: "4.9w" },
];
