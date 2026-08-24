import { useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import styles from "./Analysis.module.css";

const tabs = [
  { key: "summary", label: "综合研判", mark: "综" },
  { key: "content", label: "内容鉴真", mark: "真" },
  { key: "intent", label: "攻击意图链", mark: "链" },
  { key: "evidence", label: "证据图谱", mark: "证" },
];

const materials = [
  { id: "M-01", name: "工作人员资质图", type: "图像", cells: ["高", "缺失", "—", "高", "充分"] },
  { id: "M-02", name: "客服通话录音", type: "音频", cells: ["高", "未发现", "—", "高", "充分"] },
  { id: "M-03", name: "安全核验链接", type: "链接", cells: ["—", "—", "高", "高", "充分"] },
];

const collaborationLanes = [
  { name: "研判协调", tone: "blue", tasks: [{ left: 1, width: 17, label: "拆解缺口" }, { left: 79, width: 19, label: "停止判断" }] },
  { name: "内容鉴真", tone: "violet", tasks: [{ left: 14, width: 27, label: "图像定位" }, { left: 43, width: 23, label: "音频鉴真" }] },
  { name: "网络威胁", tone: "cyan", tasks: [{ left: 19, width: 17, label: "域名解析" }, { left: 39, width: 35, label: "页面与证书核验" }] },
  { name: "认知诱导", tone: "amber", tasks: [{ left: 10, width: 26, label: "事件抽取" }, { left: 39, width: 31, label: "意图关系校验" }] },
];

const matrixTone = (value) => {
  if (value === "高") return "danger";
  if (value === "中" || value === "待补充" || value === "缺失") return "warning";
  if (value === "充分") return "safe";
  return "muted";
};

const PanelTitle = ({ title, meta }) => (
  <div className={styles.panelTitle}><h3>{title}</h3>{meta && <span>{meta}</span>}</div>
);

const Summary = () => (
  <div className={styles.summaryGrid}>
    <section className={styles.riskPanel}>
      <div className={styles.riskRing}><div><strong>高风险</strong><span>综合攻击风险</span></div></div>
      <div className={styles.riskFacts}>
        <h3>风险结构</h3>
        {[["内容伪造",84,"violet"],["网络载荷",91,"red"],["认知诱导",89,"amber"],["证据充分性",88,"cyan"]].map(([name,value,tone]) => (
          <div className={styles.metricRow} key={name}>
            <span>{name}</span><div><i className={styles[tone]} style={{ width: `${value}%` }} /></div><strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>

    <section className={styles.claimPanel}>
      <PanelTitle title="关键结论" meta="4 项主张已审计" />
      <div className={styles.claimItem}><i className={styles.claimHigh}>01</i><div><strong>资质图存在局部合成与版面篡改线索</strong><span>IMG-HEAT-01 · META-01 · OCR-02</span></div><b>已支持</b></div>
      <div className={styles.claimItem}><i className={styles.claimHigh}>02</i><div><strong>演示链接指向凭据收集页面</strong><span>URL-03 · DOMAIN-03 · PAGE-04</span></div><b>已支持</b></div>
      <div className={styles.claimItem}><i className={styles.claimMid}>03</i><div><strong>通话音频存在合成语音异常</strong><span>AUDIO-02 · 00:08—00:13</span></div><b>已支持</b></div>
      <div className={styles.claimItem}><i className={styles.claimLow}>04</i><div><strong>用户账号已经泄露</strong><span>未发现输入凭据或扫码访问证据</span></div><b className={styles.retracted}>已撤回</b></div>
    </section>
  </div>
);

const Matrix = () => (
  <section className={styles.matrixCard}>
    <div className={styles.panelTitle}>
      <h3>材料风险矩阵</h3>
      <div className={styles.legend}><span className={styles.dotDanger} />高风险<span className={styles.dotWarning} />需关注<span className={styles.dotSafe} />证据充分</div>
    </div>
    <div className={styles.matrixTable}>
      <div className={styles.matrixHeader}><span>材料</span><span>内容真实性</span><span>来源标识</span><span>网络载荷</span><span>认知诱导</span><span>证据质量</span></div>
      {materials.map((material) => (
        <div className={styles.matrixRow} key={material.id}>
          <div className={styles.materialName}><i>{material.type.slice(0,1)}</i><span><strong>{material.name}</strong><small>{material.id}</small></span></div>
          {material.cells.map((cell,index) => <button type="button" key={`${material.id}-${index}`} className={styles[matrixTone(cell)]}>{cell}</button>)}
        </div>
      ))}
    </div>
  </section>
);

const CollaborationOverview = () => (
  <section className={styles.collaborationCard}>
    <div className={styles.collaborationHead}>
      <div><span className={styles.sectionKicker}>受控协同过程</span><h3>证据门控选择深度研判路径</h3></div>
      <div className={styles.collabStatus}><i />4个角色完成协作<b>12.8 秒</b></div>
    </div>
    <div className={styles.gateRibbon}>
      <div><i>1</i><span><strong>快速检查</strong><small>材料结构化</small></span><b>完成</b></div>
      <div><i>2</i><span><strong>工具核验</strong><small>专项工具并行</small></span><b>完成</b></div>
      <div className={styles.gateSelected}><i>3</i><span><strong>深度研判</strong><small>冲突与高影响主张补证</small></span><b>已选择</b></div>
    </div>
    <div className={styles.laneScale}><span>0s</span><span>3s</span><span>6s</span><span>9s</span><span>12s</span></div>
    <div className={styles.lanes}>
      {collaborationLanes.map((lane) => (
        <div className={styles.lane} key={lane.name}>
          <strong><i className={styles[lane.tone]} />{lane.name}</strong>
          <div>{lane.tasks.map((task) => <span className={styles[lane.tone]} key={task.label} style={{ left: `${task.left}%`, width: `${task.width}%` }}>{task.label}</span>)}</div>
        </div>
      ))}
    </div>
    <div className={styles.collabFoot}>
      <span><i>✓</i>高风险主张均有直接证据</span><span><i>✓</i>用户动作状态已确认</span><span><i>✓</i>继续调用不再增加有效证据</span><b>停止条件 4 / 4</b>
    </div>
  </section>
);

const OverviewTab = () => (
  <div className={styles.tabContent}>
    <Summary />
    <Matrix />
    <CollaborationOverview />
    <div className={styles.overviewBottom}>
      <section className={styles.chainPreview}>
        <PanelTitle title="攻击意图链" meta="点击左侧分页查看完整关系" />
        <div className={styles.miniChain}>{["身份塑造","紧迫操控","凭据请求","目标资产"].map((item,index) => <div key={item}><i>{index+1}</i><strong>{item}</strong>{index<3&&<span>→</span>}</div>)}</div>
      </section>
      <section className={styles.actionPanel}>
        <PanelTitle title="立即行动" meta="按用户尚未操作的状态生成" />
        <ol><li><i>1</i><span>不要打开链接，不要提交验证码或账号密码</span></li><li><i>2</i><span>通过银行官方应用或客服电话独立核验身份</span></li><li><i>3</i><span>保留图片、录音和原始消息作为后续材料</span></li></ol>
      </section>
    </div>
  </div>
);

const spectralColumns = Array.from({ length: 64 }, (_, index) => 26 + ((index * 37) % 64));

const ContentTab = () => {
  const [viewMode, setViewMode] = useState("heatmap");
  const modes = [{ key: "original", label: "原始图像" },{ key: "residual", label: "噪声残差" },{ key: "heatmap", label: "伪造定位" }];
  return (
    <div className={styles.tabContent}>
      <section className={styles.visualForensics}>
        <div className={styles.forensicStage}>
          <div className={styles.forensicHeader}><div><span className={styles.sectionKicker}>图像取证</span><h3>工作人员资质证明.jpg</h3></div><span className={styles.highBadge}>发现 3 处异常区域</span></div>
          <div className={[styles.imageViewport, styles[viewMode]].join(" ")}>
            <img src="/demo/fictional-bank-credential.jpg" alt="虚构银行工作人员资质证明演示图" />
            <div className={styles.scanGrid} /><div className={styles.scanBeam} />
            {viewMode === "heatmap" && <>
              <span className={[styles.heatBlob,styles.faceHeat].join(" ")} /><span className={[styles.heatBlob,styles.sealHeat].join(" ")} /><span className={[styles.heatBlob,styles.textHeat].join(" ")} />
              <span className={[styles.regionBox,styles.faceBox].join(" ")}><b>R1</b></span><span className={[styles.regionBox,styles.sealBox].join(" ")}><b>R2</b></span><span className={[styles.regionBox,styles.textBox].join(" ")}><b>R3</b></span>
            </>}
            <div className={styles.viewportHud}><span>图像 1536 × 1024</span><span>局部伪造定位已完成</span></div>
          </div>
          <div className={styles.modeRail}>
            {modes.map((mode) => <button type="button" onClick={() => setViewMode(mode.key)} className={viewMode===mode.key?styles.modeActive:""} key={mode.key}><span className={styles[`${mode.key}Thumb`]}><img src="/demo/fictional-bank-credential.jpg" alt="" /></span><strong>{mode.label}</strong></button>)}
          </div>
        </div>

        <aside className={styles.artifactInspector}>
          <PanelTitle title="区域解释" meta="可回指像素位置" />
          <div className={styles.verdictBlock}><span>图像伪造风险</span><strong>高</strong><b>局部合成与版面篡改并存</b></div>
          {[{id:"R1",name:"人物照片边界",value:87,detail:"发丝边缘与背景噪声不连续"},{id:"R2",name:"印章叠加区域",value:82,detail:"频域纹理与纸张底纹不一致"},{id:"R3",name:"编号文本区域",value:76,detail:"字符基线与压缩残差异常"}].map((region) => (
            <div className={styles.regionMetric} key={region.id}><div><i>{region.id}</i><span><strong>{region.name}</strong><small>{region.detail}</small></span><b>{region.value}</b></div><p><span style={{width:`${region.value}%`}} /></p></div>
          ))}
          <div className={styles.modelSignals}><span>局部注意热力</span><span>噪声残差</span><span>频域异常</span><span>版面一致性</span></div>
          <div className={styles.boundaryNote}><strong>判断边界</strong><p>定位图表示模型关注和异常贡献区域，需要结合来源凭证与版面核验共同形成结论。</p></div>
        </aside>
      </section>

      <section className={styles.audioLab}>
        <div className={styles.spectrogramCard}>
          <div className={styles.forensicHeader}><div><span className={styles.sectionKicker}>音频取证</span><h3>客服通话录音.mp3</h3></div><span className={styles.timeBadge}>异常区间 00:08—00:13</span></div>
          <div className={styles.spectrogramShell}>
            <div className={styles.frequencyAxis}><span>8k</span><span>4k</span><span>2k</span><span>0</span></div>
            <div className={styles.spectrogram}>
              {spectralColumns.map((height,index) => <i key={index} style={{ height: `${height}%`, opacity: .45 + (height % 30) / 60 }} />)}
              <div className={styles.audioFocus}><span>相位与谐波异常</span></div><div className={styles.audioCursor} />
            </div>
          </div>
          <svg className={styles.waveform} viewBox="0 0 1000 105" preserveAspectRatio="none" aria-label="音频波形"><path d="M0 52 L20 44 L35 66 L52 24 L68 78 L87 49 L103 61 L121 17 L139 86 L158 45 L177 69 L196 29 L216 72 L235 19 L253 89 L272 41 L291 67 L310 47 L329 61 L347 14 L365 94 L383 9 L401 98 L420 16 L438 91 L457 11 L475 95 L494 22 L512 83 L531 31 L549 75 L568 45 L587 62 L606 20 L625 87 L644 36 L663 74 L682 27 L701 82 L720 43 L739 67 L758 31 L777 85 L796 48 L815 64 L834 18 L853 91 L872 39 L891 72 L910 31 L929 81 L948 46 L967 63 L985 48 L1000 54" /></svg>
          <div className={styles.timelineMarks}><span>00:00</span><span>00:06</span><span>00:12</span><span>00:18</span><span>00:24</span></div>
        </div>
        <aside className={styles.audioEvidence}>
          <PanelTitle title="可解释音频线索" meta="3 项相互印证" />
          <div><i className={styles.audioRed}>01</i><span><strong>谐波连续性</strong><small>高频谐波出现非自然截断</small></span><b>异常</b></div>
          <div><i className={styles.audioAmber}>02</i><span><strong>相位一致性</strong><small>辅音转换处出现局部相位跳变</small></span><b>异常</b></div>
          <div><i className={styles.audioBlue}>03</i><span><strong>呼吸与韵律</strong><small>语句间隔过于规则，呼吸线索不足</small></span><b>可疑</b></div>
          <div className={styles.audioSummary}><span>综合判断</span><strong>存在合成语音线索</strong><p>仅凭当前录音不能确认说话人真实身份，需通过官方渠道独立核验。</p></div>
        </aside>
      </section>

      <div className={styles.contentBottomGrid}>
        <section className={styles.sourceCard}>
          <PanelTitle title="来源与生成标识" meta="独立于模型结论" />
          <div className={styles.sourceFlow}><div><i>1</i><span><strong>文件元数据</strong><small>创建软件字段与时间链不完整</small></span><b>异常</b></div><div><i>2</i><span><strong>生成内容标识</strong><small>未发现有效显式或隐式标识</small></span><b>缺失</b></div><div><i>3</i><span><strong>来源凭证</strong><small>未发现可验证的 C2PA 凭证</small></span><b>不足</b></div></div>
        </section>
        <section className={styles.consistencyCard}>
          <PanelTitle title="跨材料身份一致性" meta="图像 · 音频 · 链接" />
          <div className={styles.identityMap}><div className={styles.identityCenter}><strong>“银行工作人员”</strong><span>核心身份主张</span></div><div className={styles.identityNodeOne}><i>图</i><strong>资质图</strong><span>身份来源不可验证</span></div><div className={styles.identityNodeTwo}><i>音</i><strong>通话录音</strong><span>自称客服林经理</span></div><div className={styles.identityNodeThree}><i>链</i><strong>核验链接</strong><span>bank-service.example</span></div><svg viewBox="0 0 600 210"><path d="M300 102 C225 80 185 58 105 45 M300 102 C375 80 415 58 495 45 M300 102 C300 150 300 155 300 188" /></svg></div>
        </section>
      </div>
    </div>
  );
};

const IntentTab = () => {
  const [active, setActive] = useState(4);
  const [intentMode, setIntentMode] = useState("evidence");
  const stages = [
    { title:"目标接触", evidence:"TEXT-01", detail:"通过私聊发送“账户异常”通知，识别持有银行账户的目标用户。", tone:"cyan", status:"已观察", tactic:"接触与筛选" },
    { title:"身份塑造", evidence:"IMG-01", detail:"使用伪造工作人员资质证明构造银行从业者身份。", tone:"blue", status:"已观察", tactic:"权威身份冒充" },
    { title:"信任强化", evidence:"AUDIO-02", detail:"通话中使用合成语音和专业话术强化身份可信度。", tone:"violet", status:"已观察", tactic:"跨模态一致性伪装" },
    { title:"紧迫施压", evidence:"ASR-04", detail:"以“限时冻结”和“立即处理”压缩用户独立核验时间。", tone:"amber", status:"已观察", tactic:"紧迫感操控" },
    { title:"凭据请求", evidence:"URL-03", detail:"发送核验页面并要求输入账号、密码及短信验证码。", tone:"red", status:"已观察", tactic:"凭据窃取" },
    { title:"账户接管", evidence:"TGT-01", detail:"若用户提交凭据，攻击者可能进一步尝试账户接管与资金操作。", tone:"red", status:"条件推演", tactic:"目标资产控制" },
  ];
  const signalTracks = [
    { name:"文本事件", tone:"cyan", start:1, end:5, label:"异常通知 → 限时处理" },
    { name:"资质图片", tone:"blue", start:2, end:4, label:"身份凭证塑造" },
    { name:"通话音频", tone:"violet", start:3, end:5, label:"身份强化 → 情绪施压" },
    { name:"演示链接", tone:"red", start:5, end:7, label:"凭据收集页面" },
  ];
  return (
    <div className={styles.tabContent}>
      <section className={styles.intentWorkbench}>
        <div className={styles.intentHeader}>
          <div><span className={styles.sectionKicker}>攻击关系推演</span><h3>六阶段意图链与多材料证据映射</h3></div>
          <div className={styles.intentModes}>{[["chain","主链"],["evidence","证据映射"],["branch","推演分支"]].map(([key,label]) => <button type="button" className={intentMode===key?styles.intentModeActive:""} onClick={()=>setIntentMode(key)} key={key}>{label}</button>)}</div>
        </div>
        <div className={styles.intentWorkbenchBody}>
          <div className={[styles.intentCanvas,styles[`${intentMode}Mode`]].join(" ")}>
            <div className={styles.intentFlow}>{stages.map((stage,index) => <button type="button" className={[styles.intentNode,active===index?styles.intentActive:"",stage.status==="条件推演"?styles.intentHypothesis:""].filter(Boolean).join(" ")} onClick={() => setActive(index)} key={stage.title}><span className={styles[stage.tone]}>{index+1}</span><strong>{stage.title}</strong><small>{stage.evidence}</small><em>{stage.status}</em>{index<stages.length-1&&<i>›</i>}</button>)}</div>
            <div className={styles.signalTracks}>
              <div className={styles.trackAxis}><span>证据轨道</span>{stages.map((stage,index)=><b key={stage.title}>0{index+1}</b>)}</div>
              {signalTracks.map((track)=><div className={styles.signalTrack} key={track.name}><strong><i className={styles[track.tone]}/>{track.name}</strong><div>{<span className={styles[track.tone]} style={{gridColumn:`${track.start} / ${track.end}`}}>{track.label}</span>}</div></div>)}
            </div>
            <div className={styles.outcomeBranch}>
              <span>用户当前状态</span><div className={styles.actualOutcome}><i>✓</i><strong>未打开链接</strong><small>攻击链在凭据请求前中断</small></div>
              <b>条件分支</b><div className={styles.projectedOutcome}><i>!</i><strong>若提交凭据</strong><small>凭据泄露 → 账户接管 → 资金风险</small></div>
            </div>
          </div>
          <aside className={styles.intentInspector}>
            <div className={styles.inspectorStage}><span className={styles[stages[active].tone]}>{active+1}</span><div><small>当前节点</small><strong>{stages[active].title}</strong></div><b>{stages[active].status}</b></div>
            <p>{stages[active].detail}</p>
            <dl><div><dt>证据回指</dt><dd>{stages[active].evidence}</dd></div><div><dt>攻击手段</dt><dd>{stages[active].tactic}</dd></div><div><dt>因果强度</dt><dd>{active===5?"条件关系":"0."+(91-active*2)}</dd></div><div><dt>用户动作</dt><dd>{active<5?"未跟随请求":"未发生"}</dd></div></dl>
            <div className={styles.causalGauge}><span>节点支持度</span><strong>{active===5?"推演":"充分"}</strong><i><b style={{width:active===5?"58%":"91%"}}/></i></div>
            <button type="button">查看 {stages[active].evidence} 原始位置</button>
          </aside>
        </div>
      </section>
      <section className={styles.progressionCard}>
        <div><span className={styles.sectionKicker}>风险推进曲线</span><h3>身份可信感与行为危险度在第四阶段后发生反转</h3></div>
        <svg viewBox="0 0 1000 180" preserveAspectRatio="none"><defs><linearGradient id="intentArea" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#fb7185" stopOpacity=".32"/><stop offset="1" stopColor="#fb7185" stopOpacity="0"/></linearGradient></defs><path className={styles.intentArea} d="M0 165 C120 160 160 148 250 142 S430 105 500 112 S670 70 750 76 S910 26 1000 20 L1000 180 L0 180Z"/><path className={styles.intentLine} d="M0 165 C120 160 160 148 250 142 S430 105 500 112 S670 70 750 76 S910 26 1000 20"/></svg>
        <div className={styles.progressLabels}><span>目标接触</span><span>身份塑造</span><span>信任强化</span><span>紧迫施压</span><span>凭据请求</span><span>账户接管</span></div>
      </section>
      <div className={styles.stateGrid}><section><div className={styles.stateIcon}>意</div><span>攻击者意图</span><strong>凭据窃取与账户接管诱导</strong><b className={styles.stateHigh}>已观察</b></section><section><div className={styles.stateIcon}>行</div><span>用户实际动作</span><strong>尚未打开链接或输入凭据</strong><b className={styles.stateSafe}>未执行</b></section><section><div className={styles.stateIcon}>果</div><span>实际影响</span><strong>无账号泄露或资金损失证据</strong><b className={styles.stateNeutral}>未确认损害</b></section></div>
    </div>
  );
};

const graphNodes = [
  {id:"M-01",x:75,y:125,type:"material",label:"资质图",detail:"工作人员资质证明.jpg",score:"原始",status:"已固定"},{id:"M-02",x:75,y:315,type:"material",label:"通话音频",detail:"客服通话录音.mp3",score:"原始",status:"已固定"},{id:"M-03",x:75,y:505,type:"material",label:"消息与链接",detail:"用户提交的文本与演示域名",score:"原始",status:"已固定"},
  {id:"F-01",x:255,y:75,type:"feature",label:"照片边界",detail:"发丝边缘噪声不连续",score:"0.87",status:"异常"},{id:"F-02",x:255,y:170,type:"feature",label:"印章残差",detail:"印章与纸张频域纹理冲突",score:"0.82",status:"异常"},{id:"F-03",x:255,y:265,type:"feature",label:"谐波截断",detail:"高频谐波出现非自然截断",score:"0.84",status:"异常"},{id:"F-04",x:255,y:360,type:"feature",label:"韵律异常",detail:"呼吸与语句间隔过于规则",score:"0.78",status:"可疑"},{id:"F-05",x:255,y:455,type:"feature",label:"主体不符",detail:"域名与声称银行主体无关",score:"0.93",status:"异常"},{id:"F-06",x:255,y:550,type:"feature",label:"凭据表单",detail:"页面索取密码与短信验证码",score:"0.96",status:"高危"},
  {id:"T-01",x:470,y:110,type:"analysis",label:"图像取证",detail:"局部注意、残差和版面联合",score:"0.89",status:"完成"},{id:"T-02",x:470,y:230,type:"analysis",label:"来源核验",detail:"元数据与生成内容标识解析",score:"0.76",status:"完成"},{id:"T-03",x:470,y:350,type:"analysis",label:"音频鉴真",detail:"频谱、相位与韵律联合",score:"0.86",status:"完成"},{id:"T-04",x:470,y:470,type:"analysis",label:"域名核验",detail:"注册主体、TLS与跳转链",score:"0.94",status:"完成"},{id:"T-05",x:470,y:570,type:"analysis",label:"页面分析",detail:"表单字段与提交目标解析",score:"0.95",status:"完成"},
  {id:"C-01",x:720,y:105,type:"claim",label:"身份冒充",detail:"多材料共同塑造虚假身份",score:"0.92",status:"已支持"},{id:"C-02",x:720,y:260,type:"claim",label:"合成语音",detail:"音频存在合成异常线索",score:"0.86",status:"已支持"},{id:"C-03",x:720,y:415,type:"claim",label:"凭据窃取",detail:"链接和页面指向凭据收集",score:"0.95",status:"已支持"},{id:"C-04",x:720,y:555,type:"claimWeak",label:"账号已泄露",detail:"缺少用户执行和后果证据",score:"不足",status:"已撤回"},
  {id:"A-01",x:970,y:145,type:"action",label:"停止访问",detail:"不要打开演示链接",score:"优先",status:"建议"},{id:"A-02",x:970,y:325,type:"action",label:"官方核验",detail:"通过银行官方入口核验",score:"优先",status:"建议"},{id:"A-03",x:970,y:505,type:"action",label:"保留材料",detail:"保存图片、音频和原消息",score:"必要",status:"建议"},
];
const graphLinks = [
  {from:"M-01",to:"F-01",type:"support"},{from:"M-01",to:"F-02",type:"support"},{from:"M-02",to:"F-03",type:"support"},{from:"M-02",to:"F-04",type:"support"},{from:"M-03",to:"F-05",type:"support"},{from:"M-03",to:"F-06",type:"support"},
  {from:"F-01",to:"T-01",type:"support"},{from:"F-02",to:"T-01",type:"support"},{from:"M-01",to:"T-02",type:"correlate"},{from:"F-03",to:"T-03",type:"support"},{from:"F-04",to:"T-03",type:"correlate"},{from:"F-05",to:"T-04",type:"support"},{from:"F-06",to:"T-05",type:"support"},
  {from:"T-01",to:"C-01",type:"support"},{from:"T-02",to:"C-01",type:"correlate"},{from:"T-03",to:"C-01",type:"correlate"},{from:"T-03",to:"C-02",type:"support"},{from:"T-04",to:"C-03",type:"support"},{from:"T-05",to:"C-03",type:"support"},{from:"C-03",to:"C-04",type:"conflict"},
  {from:"C-01",to:"A-02",type:"support"},{from:"C-02",to:"A-02",type:"correlate"},{from:"C-03",to:"A-01",type:"support"},{from:"C-03",to:"A-03",type:"support"},{from:"C-04",to:"A-03",type:"conflict"},
];

const EvidenceTab = () => {
  const [selected,setSelected] = useState(graphNodes.find((node)=>node.id==="C-03"));
  const nodeById = (id) => graphNodes.find((node) => node.id===id);
  const relatedLinks = graphLinks.filter((link)=>link.from===selected.id||link.to===selected.id);
  return (
    <div className={styles.tabContent}>
      <section className={styles.graphCard}>
        <div className={styles.graphTop}><div><span className={styles.sectionKicker}>证据可回溯</span><h3>材料—局部特征—工具结果—主张—行动</h3></div><div className={styles.graphTools}><button type="button" className={styles.graphToolActive}>风险路径</button><button type="button">全部关系</button><button type="button">自动布局</button><span>21 节点 · 25 关系</span></div></div>
        <div className={styles.graphLegend}><span><i className={styles.legendSupport}/>直接支持</span><span><i className={styles.legendCorrelate}/>关联印证</span><span><i className={styles.legendConflict}/>冲突或不足</span><b>点击节点查看证据详情</b></div>
        <div className={styles.graphBody}>
          <div className={styles.graphCanvas}><div className={styles.graphColumns}><span>原始材料</span><span>局部特征</span><span>工具结果</span><span>风险主张</span><span>行动建议</span></div><svg viewBox="0 0 1050 630" className={styles.evidenceGraph} aria-label="证据关系图"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#536077"/></marker><marker id="arrowConflict" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#fb7185"/></marker></defs>{graphLinks.map((link)=>{const source=nodeById(link.from);const target=nodeById(link.to);const active=selected.id===link.from||selected.id===link.to;return <path key={link.from+link.to} d={`M${source.x} ${source.y} C${source.x+72} ${source.y} ${target.x-72} ${target.y} ${target.x} ${target.y}`} className={[styles.graphLink,styles[`link${link.type}`],active?styles.graphLinkActive:""].filter(Boolean).join(" ")} markerEnd={link.type==="conflict"?"url(#arrowConflict)":"url(#arrow)"}/>;})}{graphNodes.map((node)=>{const connected=relatedLinks.some((link)=>link.from===node.id||link.to===node.id);return <g key={node.id} className={[styles.graphNode,styles[node.type],selected.id===node.id?styles.graphNodeSelected:"",connected?styles.graphNodeConnected:""].filter(Boolean).join(" ")} onClick={()=>setSelected(node)} role="button" tabIndex="0"><circle cx={node.x} cy={node.y} r={node.type==="feature"?30:35}/><circle className={styles.nodePulse} cx={node.x} cy={node.y} r={node.type==="feature"?38:43}/><text x={node.x} y={node.y-1} textAnchor="middle">{node.label}</text><text x={node.x} y={node.y+15} textAnchor="middle" className={styles.nodeId}>{node.id}</text></g>;})}</svg><div className={styles.graphMiniMap}>{[0,1,2,3,4].map((item)=><i key={item}/>)}<span/></div></div>
          <aside className={styles.nodeDrawer}><span className={styles[selected.type]}>{selected.type==="material"?"原始材料":selected.type==="feature"?"局部特征":selected.type==="analysis"?"工具结果":selected.type==="claim"||selected.type==="claimWeak"?"风险主张":"行动建议"}</span><h4>{selected.label}</h4><b>{selected.id}</b><p className={styles.nodeDescription}>{selected.detail}</p><div className={styles.nodeScore}><span>证据强度</span><strong>{selected.score}</strong><i><b style={{width:selected.score==="不足"?"34%":selected.score==="原始"?"100%":`${Number.parseFloat(selected.score)*100||82}%`}}/></i></div><dl><div><dt>关联关系</dt><dd>{relatedLinks.length} 条</dd></div><div><dt>当前状态</dt><dd>{selected.status}</dd></div><div><dt>来源范围</dt><dd>本次用户材料</dd></div><div><dt>审计结果</dt><dd>{selected.type==="claimWeak"?"证据不足":"引用有效"}</dd></div></dl><div className={styles.relatedEvidence}><strong>直接关系</strong>{relatedLinks.slice(0,4).map((link)=>{const other=nodeById(link.from===selected.id?link.to:link.from);return <button type="button" onClick={()=>setSelected(other)} key={link.from+link.to}><i className={styles[`legend${link.type[0].toUpperCase()+link.type.slice(1)}`]}/><span>{other.id}</span><b>{other.label}</b></button>;})}</div><button type="button">查看原始位置</button></aside>
        </div>
      </section>
    </div>
  );
};

const Analysis = () => {
  const [activeTab,setActiveTab] = useState("summary");
  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <header className={styles.pageHeader}>
          <div><div className={styles.breadcrumb}><Link to="/detect">智能体研判</Link><span>/</span><b>VT-2026-0824-03</b></div><h1>研判详情</h1><p>虚构银行工作人员身份核验诱导 · 深度研判</p></div>
          <div className={styles.caseMeta}><span><i className={styles.onlineDot}/>研判完成</span><span>3份材料</span><span>18项证据</span><span className={styles.reportReady}>报告已生成</span><Link to="/reports">查看报告</Link></div>
        </header>
        <div className={styles.analysisLayout}>
          <nav className={styles.tabRail} aria-label="研判详情分页">
            <div className={styles.railCase}><span>当前案件</span><strong>高风险</strong><small>证据充分性 88</small></div>
            {tabs.map((tab,index)=><button type="button" className={activeTab===tab.key?styles.tabActive:""} onClick={()=>setActiveTab(tab.key)} key={tab.key}><i>{tab.mark}</i><span><strong>{tab.label}</strong><small>0{index+1}</small></span><b>›</b></button>)}
            <div className={styles.railProgress}><span>研判完整度</span><strong>100%</strong><i><b/></i><small>报告已自动归档</small></div>
          </nav>
          <div className={styles.tabViewport} key={activeTab}>{activeTab==="summary"&&<OverviewTab/>}{activeTab==="content"&&<ContentTab/>}{activeTab==="intent"&&<IntentTab/>}{activeTab==="evidence"&&<EvidenceTab/>}</div>
        </div>
      </main>
    </div>
  );
};

export default Analysis;
