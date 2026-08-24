// Home.jsx - 优化样式版本

import { useNavigate } from "react-router-dom";
import { useRef } from "react";

import splitText from "../../utils/splitText";
import LogoPoint from "../../components/LogoPoint/LogoPoint";
import CaseColumn from "../../components/CaseColumn/CaseColumn";
import BackBtn from "../../components/BackBtn/BackBtn";
import Nav from "../../layouts/Nav/Nav";

import styles from "./Home.module.css";

const Icon = () => {
  return (
    <svg
      t="1776941027484"
      className="icon"
      viewBox="0 0 1024 1024"
      version="1.1"
      xmlns="http://www.w3.org/2000/svg"
      p-id="7214"
      width="60"
      height="60"
    >
      <path
        d="M756.736 812.032L512 567.296 267.776 811.52c-12.8 12.8-28.672 7.168-45.568-9.728-16.896-16.896-23.04-32.768-9.728-45.568L456.704 512 211.968 267.264c-14.848-15.36-6.144-30.208 8.704-45.568 16.896-16.896 30.72-25.6 46.592-10.24L512 456.704 756.736 212.48c14.336-14.336 28.672-7.168 47.104 11.264 15.36 15.36 23.552 28.672 8.192 44.032L567.296 512 811.52 756.224c15.36 15.36 8.704 28.672-8.192 46.08-16.896 17.408-33.792 22.528-46.592 9.728z"
        fill="#fff"
        opacity="0.75"
        p-id="7215"
      ></path>
    </svg>
  );
};

const Home = () => {
  const navigate = useNavigate();

  const homeRef = useRef(null);

  const caseData = {
    line1: [
      {
        score: "98%",
        time: "2026-03-28",
        category: "AI语音诈骗",
        title: "AI拟声冒充孙子，七旬老人被骗2万元养老金",
        source: "湖北省人民检察院",
        readCount: "2.3k",
        confidenceReason:
          "✅ 已破案，诈骗分子落网\n✅ 有完整通话录音和嫌疑人供述\n✅ 公安机关已确认AI拟声技术\n✅ 资金流向可追溯",
        text: "【案件经过】\n2026年3月25日，家住武汉市武昌区的丁阿姨（72岁）家中座机突然响起。电话那头传来'孙子'带着哭腔的声音：'奶奶，我在学校和同学打架，把人打伤了，对方要4万元私了，不然就要报警抓我！'\n\n丁阿姨一听是孙子的声音，顿时慌了神。对方还特意嘱咐：'奶奶千万别告诉爸妈，我怕他们骂我。'半小时后，一名自称'律师助理'的男子上门取走了2万元现金。\n\n直至当晚，真正的孙子放学回家，丁阿姨才发现自己遭遇了骗局。\n\n【诈骗手法】\n经公安机关侦查，诈骗分子使用了AI拟声技术，通过网络获取受害人孙子的语音片段（如抖音、朋友圈视频），通过AI模型合成逼真的声音。老年人对AI技术的认知不足，难以分辨声音真伪，再加上'紧急救场'的焦虑感，导致骗局屡屡得手。\n\n【警方提醒】\n⚠️ 凡是接到'亲人出事'要求转账的电话，务必通过其他渠道核实！\n⚠️ 建议家人与老人约定转账'暗号'或'密语'！\n⚠️ 提醒家中老人不要随意在网上发布带有本人声音的视频！",
        imageUrl: "icons/AI拟声.jpg",
      },
      {
        score: "96%",
        time: "2026-03-27",
        category: "AI换脸诈骗",
        title: "AI换脸冒充表哥借钱，小伙险被骗5万元",
        source: "国家反诈中心",
        readCount: "1.8k",
        confidenceReason:
          "✅ 受害人提供了完整视频聊天记录\n✅ 公安机关已提取AI合成视频证据\n✅ 技术鉴定确认为Deepfake\n✅ 已锁定嫌疑人IP地址",
        text: "【案件经过】\n2026年3月26日晚，杭州小伙小张接到'表哥'的微信视频通话。视频中，'表哥'的脸和声音都一模一样，说生意上周转困难，急需5万元救急，明天就还。\n\n小张起初有些犹豫，但'表哥'在视频里表现得非常着急，还发来了身份证照片。幸好小张多问了一句：'上周我们一起吃饭，最后吃了什么？'对方愣了一下，支支吾吾答不上来。小张立刻挂断电话，拨打表哥手机核实，发现表哥根本没找他借钱。\n\n【诈骗手法】\n诈骗分子利用AI换脸和AI拟声技术，通过社交平台获取受害人亲友的照片和语音样本，合成逼真的视频进行诈骗。这种技术门槛正在降低，普通人难以分辨。\n\n【警方提醒】\n⚠️ 视频通话时让对方做特定动作（摸鼻子、转头、眨眼）！\n⚠️ 询问只有你们知道的私密信息！\n⚠️ 设置转账'二次确认'机制，大额转账必须电话或当面确认！",
        imageUrl: "icons/AI诈骗.jpg",
      },
      {
        score: "92%",
        time: "2026-03-26",
        category: "刷单诈骗",
        title: "刷单返利骗局揭秘：在校大学生被骗3万元学费",
        source: "公安部反诈中心",
        readCount: "1.5k",
        confidenceReason:
          "✅ 已破案，抓获犯罪嫌疑人12名\n✅ 有完整聊天记录和转账凭证\n✅ 涉案资金被部分追回\n✅ 犯罪团伙作案手法已查清",
        text: "【案件经过】\n2026年3月，某高校大二学生小李在宿舍刷短视频时，看到一则'手机兼职，日入300+'的广告。添加对方微信后，被拉入一个'刷单福利群'。\n\n起初，小李尝试了一单50元的任务，5分钟后收到了55元返款。第二单100元，返款110元。尝到甜头后，对方说有一个'连单'任务，需要连续完成5单才能提现，每单金额逐渐增加。小李先后转账500元、2000元、8000元、10000元、9500元，累计3万元。\n\n完成5单后，对方说'系统卡单'需要再做一个'解冻单'，小李这才意识到被骗，但对方已将其拉黑。\n\n【诈骗手法】\n骗子先给小额返利获取信任，然后以'连单''解冻''保证金'等理由诱导大额投入，最后消失。这类诈骗专门针对在校大学生和宝妈群体。\n\n【警方提醒】\n⚠️ 任何要求先垫付资金的兼职都是诈骗！\n⚠️ 刷单本身就是违法行为！\n⚠️ 不要相信'动动手指就赚钱'的谎言！",
        imageUrl: "icons/刷单.jpg",
      },
      {
        score: "55%",
        time: "2026-03-25",
        category: "可疑行为",
        title: "可疑：用户收到'银行'短信，经核实为真实通知",
        source: "系统分析",
        readCount: "892",
        confidenceReason:
          "⚠️ 初步判定为可疑诈骗\n✅ 经多渠道核实确认为真实通知\n✅ 系统误报，已更新模型\n⚠️ 该案例用于训练模型降低误报率",
        text: "【案件经过】\n2026年3月24日，用户王先生收到一条来自'95588'的短信：'您尾号1234的信用卡账单已出，请及时还款，点击链接查看详情。'\n\n王先生此前收到过诈骗短信，担心这是钓鱼链接，于是通过反诈助手进行举报和分析。\n\n【AI分析】\n✅ 发送号码：经核验为工商银行官方短信号码\n✅ 链接域名：icbc.com.cn，为银行官方域名\n✅ 内容分析：账单金额与用户实际消费记录吻合\n✅ 历史行为：用户确实有该银行信用卡，且近期有消费\n\n【结论】\n综合判断为正常银行通知，低风险。建议用户通过官方APP或网银确认，养成良好的安全意识。",
        imageUrl: "icons/信用卡.jpg",
      },
      {
        score: "78%",
        time: "2026-03-24",
        category: "冒充客服",
        title: "疑似冒充客服退款诈骗，用户警惕性高未上当",
        source: "系统预警",
        readCount: "1.1k",
        confidenceReason:
          "⚠️ 用户举报，但未造成实际损失\n✅ AI分析确认诈骗特征明显\n✅ 该号码已被多人举报\n⚠️ 缺少嫌疑人落网证据",
        text: "【案件经过】\n2026年3月23日，王女士接到自称'淘宝客服'的电话，说她购买的一款面膜'质检不合格'，商家将进行三倍赔偿。对方准确说出了王女士的订单号、购买时间和商品名称。\n\n随后，对方要求王女士添加QQ，发送了一个'退款链接'，让她填写银行卡信息和验证码。王女士想起之前看过的反诈宣传，挂断电话后自行登录淘宝APP联系官方客服，确认没有所谓的'退款'活动。\n\n【AI分析】\n❌ 对方无法通过官方渠道沟通，要求使用QQ\n❌ 发送的链接域名为假冒域名（taobao-refund.com）\n❌ 要求提供银行卡密码和验证码\n\n【结论】\n综合判断为高置信度冒充客服诈骗，已将该号码标记为诈骗电话。",
        imageUrl: "icons/客服.jpg",
      },
      {
        score: "65%",
        time: "2026-03-23",
        category: "疑似诈骗",
        title: "待核实：用户收到'中奖'短信，真伪待确认",
        source: "系统分析",
        readCount: "756",
        confidenceReason:
          "⚠️ 存在诈骗特征，但缺少关键证据\n⚠️ 该平台确有抽奖活动，真假难辨\n⚠️ 用户未点击链接，无法进一步分析\n⚠️ 需人工进一步核实",
        text: "【案件经过】\n2026年3月22日，用户陈女士收到短信：'恭喜您获得XX平台10周年庆一等奖，奖金8万元！点击链接填写领奖信息，验证码：XXXX。'\n\n陈女士不确定是否为诈骗，通过反诈助手进行举报。\n\n【AI分析】\n⚠️ 发送号码：非官方短信号码，为个人手机号\n⚠️ 链接域名：经检测为仿冒域名（xxpt-anniversary.com）\n⚠️ 可疑点：要求点击链接填写个人信息\n⚠️ 存疑点：该平台近期确实在举办10周年庆活动\n\n【结论】\n综合判断为高风险，建议不要点击链接。如需核实，请通过官方渠道联系平台客服。",
        imageUrl: "icons/短信.jpg",
      },
    ],
    line2: [
      {
        score: "99%",
        time: "2026-03-28",
        category: "冒充公检法",
        title: "冒充公检法诈骗升级，独居老人被骗20万养老钱",
        source: "公安部",
        readCount: "2.1k",
        confidenceReason:
          "✅ 已破案，犯罪团伙被端\n✅ 有完整通话录音和伪造文件\n✅ 资金流向已追踪\n✅ 多个受害人指认",
        text: "【案件经过】\n2026年3月，68岁的独居老人李奶奶接到自称'上海市公安局'的电话，说她名下有一张银行卡涉嫌洗钱犯罪，涉案金额高达200万元。对方还通过微信发来了伪造的'逮捕令'和'冻结令'，上面有李奶奶的照片和身份证号。\n\n李奶奶被吓得六神无主，对方要求她将全部资金转入'安全账户'接受审查，还威胁'不能告诉任何人，否则立即逮捕'。李奶奶先后将20万元养老金转入对方提供的账户。\n\n直到银行工作人员发现异常报警，李奶奶才知道被骗，但资金已被转移。\n\n【诈骗手法】\n冒充公检法诈骗是传统的电信诈骗手法，但近年来不断升级：\n1. 使用改号软件冒充公安局、检察院电话\n2. 伪造通缉令、逮捕令等法律文书\n3. 威胁恐吓受害人，制造紧张氛围\n4. 要求转账到'安全账户'（公检法机关根本没有安全账户）\n\n【警方提醒】\n⚠️ 公检法机关不会通过电话办案！\n⚠️ 不会设立'安全账户'要求转账！\n⚠️ 不会通过微信、QQ发送法律文书！\n⚠️ 接到此类电话请立即挂断并拨打110或96110核实！",
        imageUrl: "icons/冒充公检法.png",
      },
      {
        score: "96%",
        time: "2026-03-27",
        category: "扫码诈骗",
        title: "扫码领鸡蛋？多名老人银行卡被盗刷数十万元",
        source: "新华网",
        readCount: "1.6k",
        confidenceReason:
          "✅ 已破案，抓获犯罪嫌疑人8名\n✅ 有受害人手机取证报告\n✅ 恶意软件已被分析\n✅ 涉案金额明确",
        text: "【案件经过】\n近日，济南市公安局历下分局成功破获一起针对老年人的银行卡盗刷案件。犯罪团伙在多个小区门口摆摊，以'免费领鸡蛋''扫码送大米'为诱饵，吸引老年人参与。\n\n老人扫码后，手机被偷偷安装了恶意软件。该软件不仅会窃取手机中的短信、通讯录，还会拦截银行验证码。犯罪团伙利用这些信息，将老人银行卡中的钱转走。\n\n据统计，该案受害老人达20余人，涉案金额数十万元。\n\n【诈骗手法】\n1. 以'免费礼品'吸引老年人扫码\n2. 趁机在老人手机中安装恶意软件\n3. 窃取银行卡信息和验证码\n4. 盗刷银行卡\n\n【警方提醒】\n⚠️ 切勿随意扫码陌生二维码！\n⚠️ 不要将手机交给陌生人操作！\n⚠️ 关闭手机'允许安装未知来源应用'功能！\n⚠️ 子女应帮助老人安装国家反诈中心APP并开启预警！",
        imageUrl: "icons/扫码领鸡蛋.jpeg",
      },
      {
        score: "94%",
        time: "2026-03-26",
        category: "寄递诈骗",
        title: "布娃娃腹中藏现金！新型诈骗手法曝光",
        source: "人民网",
        readCount: "1.4k",
        confidenceReason:
          "✅ 已拦截成功，证据确凿\n✅ 受害人配合调查\n✅ 有快递记录和监控视频\n⚠️ 上游诈骗分子仍在追查",
        text: "【案件经过】\n近日，达州市宣汉县公安局成功拦截一起以布娃娃藏匿现金邮寄的新型诈骗案件。\n\n快递员在收件时发现，一名中年女性寄出的布娃娃手感异常，腹部鼓起。经检查，布娃娃腹内藏有1万元现金。民警调查发现，王女士通过网络学习炒股，被'导师带投、稳赚不赔'为诱饵诱导下载虚假投资APP。\n\n诈骗分子为规避警方线上资金流侦查，要求王女士通过线下方式交付'投资款'，将现金藏于布娃娃棉花内邮寄。\n\n【诈骗手法】\n这是典型的'线上诈骗+线下取现'新型诈骗模式：\n1. 线上诱导受害人投资\n2. 要求线下交付现金、黄金等实物\n3. 通过快递、网约车等方式转移赃款\n4. 规避线上资金追踪\n\n【警方提醒】\n⚠️ 任何要求线下交付财物的'投资'都是诈骗！\n⚠️ 快递员发现异常包裹请及时报警！\n⚠️ 投资理财请选择正规金融机构！",
        imageUrl: "icons/邮递诈骗.png",
      },
      {
        score: "72%",
        time: "2026-03-25",
        category: "可疑链接",
        title: "用户点击陌生链接，反诈系统及时拦截",
        source: "反诈系统",
        readCount: "623",
        confidenceReason:
          "⚠️ 用户未输入信息，无法完全确认诈骗\n✅ 链接已被多平台标记为钓鱼网站\n✅ 系统分析确认高风险\n⚠️ 缺少用户被骗证据",
        text: "【案件经过】\n2026年3月24日，用户赵先生收到一条短信：'您的ETC已过期，请点击链接重新认证，否则将影响使用。'赵先生担心影响出行，点击了链接。\n\n页面跳转到一个看似正规的ETC认证页面，要求填写车牌号、银行卡号、密码和验证码。就在这时，反诈系统弹出红色预警：'检测到您正在访问高风险网站，请立即停止操作！'\n\n赵先生及时停止，未输入任何信息。\n\n【AI分析】\n❌ 链接域名：etc-verify.com（ETC官方为12122.com.cn）\n❌ 页面：模仿ETC官网，但存在多处拼写错误\n❌ 要求：要求填写银行卡密码（正规机构不会要求）\n\n【结论】\n综合判断为钓鱼网站诈骗，系统已将该链接加入黑名单。用户未受损失。",
        imageUrl: "icons/Etc.jpg",
      },
      {
        score: "58%",
        time: "2026-03-24",
        category: "低风险",
        title: "用户咨询：陌生电话推销理财产品",
        source: "系统分析",
        readCount: "512",
        confidenceReason:
          "⚠️ 存在夸大宣传，但非典型诈骗\n✅ 对方公司有合法资质\n✅ 产品在监管平台有备案\n⚠️ 用户未受损失，仅咨询",
        text: "【案件经过】\n2026年3月23日，用户刘先生接到一个推销电话，对方自称是某证券公司客户经理，推荐一款'年化收益8%、保本保息'的理财产品。\n\n刘先生保持警惕，未立即购买，而是通过反诈助手进行核实。\n\n【AI分析】\n⚠️ 对方公司资质：经查询，该公司确有证券投资咨询资质\n⚠️ 产品信息：该理财产品在监管平台有备案\n⚠️ 可疑点：'保本保息'承诺违反资管新规\n\n【结论】\n综合判断为正常的理财产品推销，但'保本保息'承诺存在夸大宣传嫌疑。建议用户通过正规渠道了解产品详情，谨慎投资。",
        imageUrl: "icons/理财.jpg",
      },
    ],
    line3: [
      {
        score: "97%",
        time: "2026-03-28",
        category: "追星诈骗",
        title: "追星女孩遭遇'假警察'，奶奶10万积蓄被骗光",
        source: "扬州网",
        readCount: "1.9k",
        confidenceReason:
          "✅ 已破案，抓获犯罪嫌疑人\n✅ 有完整聊天记录和转账记录\n✅ 受害人已报案\n✅ 资金流向已追踪",
        text: "【案件经过】\n13岁的小涵是某女明星的粉丝。2026年3月，她在刷短视频时看到一则消息，称'加QQ可以联系到明星本人'。小涵立即添加了对方QQ。\n\n对方自称是'明星助理'，说小涵'泄露了明星隐私'，需要配合调查。随后，一名穿着'警服'的男子与小涵视频通话，称自己是'公安局民警'，要求小涵配合调查，否则'会有案底影响一生'。\n\n涉世未深的小涵害怕不已，按照对方要求拿来奶奶的手机，躲进房间内操作，将奶奶银行卡里的10万元全部转给了对方。\n\n直到奶奶发现账户异常，才知道被骗。\n\n【诈骗手法】\n1. 利用未成年人对明星的崇拜心理\n2. 冒充明星助理、警察等身份\n3. 威胁恐吓，制造紧张氛围\n4. 诱导孩子操作家长手机转账\n\n【警方提醒】\n⚠️ 家长要留意孩子反常举动！\n⚠️ 孩子突然神情紧张索要手机，可能是正在与诈骗分子联系！\n⚠️ 孩子无故将自己反锁在房间内，要提高警惕！\n⚠️ 不要将支付密码告诉孩子！",
        imageUrl: "icons/追星.jpg",
      },
      {
        score: "95%",
        time: "2026-03-27",
        category: "AI诈骗",
        title: "AI语音合成冒充老板，财务人员被骗15万",
        source: "央视新闻",
        readCount: "1.3k",
        confidenceReason:
          "✅ 已报案，警方立案侦查\n✅ 有通话录音证据\n✅ 技术鉴定确认为AI合成语音\n⚠️ 嫌疑人仍在追查中",
        text: "【案件经过】\n2026年3月，某公司财务人员小王接到'总经理'的微信语音电话。电话那头的声音和总经理一模一样，语气也很急切：'小王，我正在和客户谈一个紧急项目，需要马上转15万定金到对方账户，稍后补流程。'\n\n小王听声音确实是总经理，没有多想就转了15万。转账后，小王遇到总经理本人，才发现总经理根本没打过电话。\n\n【诈骗手法】\n诈骗分子通过公司官网、社交平台等渠道获取总经理的语音样本（如公开演讲、采访视频），使用AI语音合成技术生成逼真的声音。\n\n【警方提醒】\n⚠️ 财务人员要严格执行财务制度！\n⚠️ 大额转账必须当面或视频确认！\n⚠️ 设置转账'双重确认'机制！\n⚠️ 定期进行反诈培训！",
        imageUrl: "icons/公司.png",
      },
      {
        score: "88%",
        time: "2026-03-26",
        category: "杀猪盘",
        title: "网恋'高富帅'诱导投资，系统及时预警挽损",
        source: "反诈系统",
        readCount: "1.1k",
        confidenceReason:
          "⚠️ 用户及时止损，未造成损失\n✅ AI分析确认诈骗模式\n✅ 对方账号已被多人举报\n⚠️ 缺少嫌疑人身份信息",
        text: "【案件经过】\n2026年3月，单身女性林女士在某交友软件认识了一位自称'金融精英'的男子。对方头像帅气，朋友圈全是豪车、美食、高端场所，自称'年薪百万'。\n\n两人聊得很投缘，对方每天嘘寒问暖，很快确立了恋爱关系。两周后，对方说自己在做一个'稳赚不赔'的投资项目，邀请林女士一起参与。林女士正准备投资5万元时，反诈系统弹出预警：'检测到您正在与疑似杀猪盘诈骗分子聊天，请提高警惕！'\n\n林女士这才意识到可能是骗局，终止了联系。\n\n【诈骗手法】\n'杀猪盘'是典型的交友诱导投资诈骗：\n1. 建立感情信任（养猪）\n2. 推荐投资平台（诱导）\n3. 小额返利获取信任（喂猪）\n4. 诱导大额投入后消失（杀猪）\n\n【警方提醒】\n⚠️ 网络交友需谨慎！\n⚠️ 涉及金钱更要警惕！\n⚠️ 不要相信'稳赚不赔'的投资！\n⚠️ 不要点击对方发送的链接或下载不明APP！",
        imageUrl: "icons/杀猪盘.jpeg",
      },
      {
        score: "82%",
        time: "2026-03-25",
        category: "虚假招聘",
        title: "'高薪兼职'骗局，应届毕业生险中招",
        source: "系统预警",
        readCount: "945",
        confidenceReason:
          "⚠️ 用户未转账，无法确认诈骗\n✅ 招聘信息存在明显异常\n✅ 对方账号已被举报\n⚠️ 缺少受害人指认",
        text: "【案件经过】\n2026年3月，应届毕业生小张在招聘网站看到一则'日结300元、时间自由、无经验要求'的兼职招聘信息。小张添加对方微信后，被告知需要先交300元'入职保证金'，'工作满一个月后退还'。\n\n小张正准备转账时，反诈系统弹出风险提示：'检测到对方账户存在异常交易记录，请谨慎转账！'小张立即停止操作。\n\n【AI分析】\n❌ 薪资明显高于市场水平（日结300元远超同类岗位）\n❌ 要求先交保证金（正规招聘不会收取任何费用）\n❌ 收款账户为个人账户（企业应有对公账户）\n❌ 该账户已被多人举报\n\n【结论】\n综合判断为虚假招聘诈骗。用户未转账，已举报该账号。",
        imageUrl: "icons/招聘.jpg",
      },
      {
        score: "45%",
        time: "2026-03-24",
        category: "正常咨询",
        title: "用户咨询：接到教育机构推销电话，经核实为正规机构",
        source: "系统分析",
        readCount: "423",
        confidenceReason:
          "⚠️ 用户咨询，非诈骗案例\n✅ 经核实为正规机构\n✅ 系统误判，已更新模型\n⚠️ 用于训练模型降低误报",
        text: "【案件经过】\n2026年3月23日，用户陈女士接到某教育机构的电话，对方推荐'Python编程培训课程'，原价8999元，'限时优惠'后5999元。\n\n陈女士不确定是否为诈骗，通过反诈助手进行核实。\n\n【AI分析】\n✅ 对方公司资质：经查询，该公司有教育培训资质\n✅ 电话来源：为官方客服号码，非改号软件\n✅ 课程信息：该课程在多个平台有售，价格合理\n✅ 无异常要求：未要求转账到个人账户\n\n【结论】\n综合判断为正常的教育培训推销电话，低风险。建议用户多方比较后再决定是否购买。",
        imageUrl: "icons/退费.jpg",
      },
    ],
  };

  return (
    <>
      <Nav className={styles.header} />
      <main className={styles.home} ref={homeRef}>
        <div className={styles.curveBackground}>
          <svg
            className={styles.curveSvg}
            viewBox="0 0 1440 800"
            preserveAspectRatio="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* 左侧曲线 */}
            <path
              d="M -100 800
             C 100 600, 200 400, 150 200
             C 100 0, 400 50, 500 100
             L 500 800
             Z"
              fill="url(#grad1)"
              opacity="0.6"
            />

            {/* 右侧曲线 */}
            <path
              d="M 1540 800
             C 1200 600, 1200 300, 1200 200
             C 1200 200, 940 100, 940 300
             L 940 800
             Z"
              fill="url(#grad2)"
              opacity="0.6"
            />

            {/* 中间装饰线 */}
            <path
              d="M -50 600
             Q 300 700, 720 580
             T 1490 550"
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="2"
              fill="none"
              strokeDasharray="5,5"
            />

            <defs>
              {/* 左侧渐变 */}
              <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#667eea" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#764ba2" stopOpacity="0.4" />
              </linearGradient>

              {/* 右侧渐变 */}
              <linearGradient id="grad2" x1="100%" y1="0%" x2="0%" y2="0%">
                <stop offset="0%" stopColor="#764ba2" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#667eea" stopOpacity="0.4" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className={styles.top}>
          <div className={styles.text}>
            <h1 className={styles.title}>{splitText("智鉴安澜")}</h1>
            <h1 className={styles.title}>{splitText("VeriTide")}</h1>
            <p className={styles.note}>
              「让每个反诈结论都有证据，让每一步行动都有依据」
            </p>
            <button
              className={styles.btn}
              onClick={() => {
                if (!localStorage.getItem("token")) {
                  navigate("/login");
                } else {
                  navigate("/detect");
                }
              }}
            >
              开始研判
            </button>
          </div>
          <div className={styles.caseBox}>
            <CaseColumn data={caseData.line1} columnIndex={0} speed="medium" />

            <CaseColumn data={caseData.line2} columnIndex={1} speed="medium" />

            <CaseColumn
              data={caseData.line3}
              columnIndex={2}
              speed="medium"
              className={styles.end}
            />
          </div>
        </div>
        <div className={styles.bottom}>
          {/* Hero Section */}
          <section className={styles.hero}>
            <div className={styles.heroContent}>
              <h1 className={styles.heroTitle}>智鉴安澜</h1>
              <p className={styles.slogan}>
                析伪辨迹，可信研判
              </p>
              <p className={styles.subtitle}>
                面向生成式AI社会工程诱导的多模态智能反诈与可信研判助手
              </p>
            </div>
            <div className={styles.heroOverlay}></div>
          </section>

          <section className={styles.logoPointSection}>
            <LogoPoint />
          </section>

          {/* Background Section */}
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>项目背景</h2>
              <div className={styles.titleUnderline}></div>
            </div>
            <div className={styles.contentCard}>
              <p className={styles.paragraph}>
                生成式AI正在把诈骗从单一话术升级为语音伪造、身份冒充、仿冒页面和恶意文件协同的复合攻击。
                普通用户面对的不再只是一段可疑文字，而是一组彼此配合的数字材料。
              </p>
              <p className={styles.paragraph}>
                智鉴安澜允许用户提交文字、截图、语音、视频、二维码、链接和文件，
                分别核验内容与来源、网络载荷、认知诱导和用户实际操作状态。
              </p>
              <p className={styles.paragraph}>
                系统不把DeepFake直接等同于诈骗，也不让大模型凭语言猜测链接和文件风险。
                每项关键结论都绑定可回指证据，在证据不足时主动降级，再给出与用户当前状态匹配的行动建议。
              </p>
            </div>
          </section>

          {/* 核心功能展示 */}
          <section className={styles.featuresSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>核心功能</h2>
              <div className={styles.titleUnderline}></div>
            </div>
            <div className={styles.featuresGrid}>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/检测.svg" alt="" />
                </div>
                <h3>多维内容鉴真</h3>
                <p>分别分析图像、音频、视频、音画一致性和生成内容来源标识</p>
              </div>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/实时预警.svg" alt="" />
                </div>
                <h3>认知诱导还原</h3>
                <p>从多轮材料中还原身份塑造、情绪操控、危险请求和目标资产</p>
              </div>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/监测.svg" alt="" />
                </div>
                <h3>链接与文件核验</h3>
                <p>通过安全工具核验二维码、跳转域名、数字签名和可执行载荷</p>
              </div>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/监护人联动.svg" alt="" />
                </div>
                <h3>受控协同分析</h3>
                <p>围绕证据缺口调度专项角色，并通过权限、预算和停止条件约束调用</p>
              </div>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/升级.svg" alt="" />
                </div>
                <h3>原子主张审计</h3>
                <p>逐项检查结论与证据引用，撤回无依据或超出用户实际动作的推断</p>
              </div>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>
                  <img src="/icons/证据链.svg" alt="" />
                </div>
                <h3>可信安全报告</h3>
                <p>形成可复核的个人研判记录，并验证报告与证据目录是否被修改</p>
              </div>
            </div>
          </section>

          {/* 问题展示区域 */}
          <section className={styles.problemSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>传统反诈的困局</h2>
              <div className={styles.titleUnderline}></div>
            </div>
            <div className={styles.problemGrid}>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>
                  <img src="/icons/滞后.svg" alt="" />
                  <div className={styles.problemIconCross}>{Icon()}</div>
                </div>
                <h3>只看单句</h3>
                <p>关键词分类无法看见多轮交互如何逐步推进到扫码、登录和安装。</p>
              </div>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>
                  <img src="/icons/覆盖分析.svg" alt="" />
                  <div className={styles.problemIconCross}>{Icon()}</div>
                </div>
                <h3>不验载荷</h3>
                <p>聊天模型可以解释话术，却不能只凭语言可靠判断域名、跳转和文件行为。</p>
              </div>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>
                  <img src="/icons/识别.svg" alt="" />
                  <div className={styles.problemIconCross}>{Icon()}</div>
                </div>
                <h3>混淆真假</h3>
                <p>AI生成内容不一定有害，真人录制内容同样可能承载高风险诱导。</p>
              </div>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>
                  <img src="/icons/无法升级.svg" alt="" />
                  <div className={styles.problemIconCross}>{Icon()}</div>
                </div>
                <h3>结论越界</h3>
                <p>观察到攻击意图不代表用户已经执行，更不能直接推断账号泄露或资金损失。</p>
              </div>
            </div>
          </section>

          {/* 技术指标可视化 */}
          <section className={styles.techSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>技术优势</h2>
              <div className={styles.titleUnderline}></div>
            </div>
            <div className={styles.techMetrics}>
              <div className={styles.metricCard}>
                <div className={styles.metricCircle}>
                  <span className={styles.metricValue}>鉴真</span>
                </div>
                <p className={styles.metricLabel}>内容与来源分离</p>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricCircle}>
                  <span className={styles.metricValue}>析链</span>
                </div>
                <p className={styles.metricLabel}>危险请求可回指</p>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricCircle}>
                  <span className={styles.metricValue}>补证</span>
                </div>
                <p className={styles.metricLabel}>安全工具受控调用</p>
              </div>
              <div className={styles.metricCard}>
                <div className={styles.metricCircle}>
                  <span className={styles.metricValue}>慎断</span>
                </div>
                <p className={styles.metricLabel}>结论主动降级</p>
              </div>
            </div>
          </section>

          {/* 适用人群 */}
          <section className={styles.usersSection}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>适用人群</h2>
              <div className={styles.titleUnderline}></div>
            </div>
            <div className={styles.userGrid}>
              <div className={styles.userCard}>
                <div className={styles.userIcon}>
                  <img src="/icons/老年人.svg" alt="" />
                </div>
                <h3>老年人</h3>
                <p>
                  核验冒充熟人、保健品退款和可疑链接，不要求理解专业安全术语
                </p>
              </div>
              <div className={styles.userCard}>
                <div className={styles.userIcon}>
                  <img src="/icons/学生.svg" alt="" />
                </div>
                <h3>学生</h3>
                <p>
                  核验游戏交易、兼职刷单、账号异常和可疑安装包
                </p>
              </div>
              <div className={styles.userCard}>
                <div className={styles.userIcon}>
                  <img src="/icons/上班.svg" alt="" />
                </div>
                <h3>上班族</h3>
                <p>核验投资理财、虚假贷款、冒充同事和钓鱼邮件</p>
              </div>
              <div className={styles.userCard}>
                <div className={styles.userIcon}>
                  <img src="/icons/监护人.svg" alt="" />
                </div>
                <h3>家庭协助者</h3>
                <p>帮助家人整理可疑材料，并获得清晰的核验与处置建议</p>
              </div>
            </div>
          </section>

          {/* CTA */}
          <section className={styles.ctaSection}>
            <h2>让每个反诈结论都有证据</h2>
            <p>现在就对可疑内容、链接和文件发起一次安全研判</p>
          </section>
        </div>

        {/* 回到顶部按钮 - 根据滚动状态显示/隐藏 */}
        <BackBtn targetRef={homeRef} scrollThreshold={600} />
      </main>
    </>
  );
};

export default Home;
