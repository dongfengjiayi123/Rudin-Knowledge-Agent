"""Rebuild source index and checked introductory graph from the supplied edition."""
import json
from pathlib import Path
from rudin_agent.ingest import parse_pdf
ROOT=Path(__file__).parent
index=parse_pdf(); lookup={n['id']:n for n in index['nodes']}
(ROOT/'data/index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),'utf8')
rows=[
('1.7','上界与下界','upper bound lower bound','在有序集 S 中，E⊂S。若存在 β∈S，使所有 x∈E 都满足 x≤β，则 β 是 E 的上界，E 称为有上界；下界和有下界类似定义。'),
('1.8','上确界与下确界','supremum infimum','设 E 是有序集 S 的有上界子集。α=sup E 当且仅当 α 是上界，且任意 γ<α 都不是 E 的上界。下确界是最大的下界。'),
('1.10','最小上界性质','least upper bound property completeness','有序集 S 具有最小上界性质，是指每个非空、有上界的 E⊂S，都存在属于 S 的 sup E。'),
('1.19','实数域的存在','real field completeness','存在具有最小上界性质的有序域 ℝ；并且它包含一个与有理数域 ℚ 同构的子域。'),
('2.15','度量空间','metric space distance','集合 X 配有函数 d:X×X→ℝ，满足：d(p,q)≥0，且 d(p,q)=0 当且仅当 p=q；d(p,q)=d(q,p)；d(p,q)≤d(p,r)+d(r,q)。这样的 (X,d) 称为度量空间。'),
('2.18.a','邻域','neighborhood open ball','在度量空间 X 中，点 p 的半径 r>0 的邻域是 Nᵣ(p)={q∈X:d(p,q)<r}。'),
('2.18.b','聚点','limit point accumulation point','p 是 E⊂X 的聚点，当且仅当 p 的每个邻域都包含某个 q∈E，且 q≠p。聚点不必属于 E。'),
('2.18.c','孤立点','isolated point','若 p∈E 且 p 不是 E 的聚点，则 p 是 E 的孤立点。'),
('2.18.d','闭集','closed set','E⊂X 是闭集，当且仅当 E 的每个聚点都属于 E。闭性相对于所在的度量空间 X 而言。'),
('2.18.e','内点','interior point','p 是 E 的内点，当且仅当存在 r>0，使 Nᵣ(p)⊂E。'),
('2.18.f','开集','open set','E⊂X 是开集，当且仅当 E 的每个点都是 E 的内点。开性取决于环境空间 X。'),
('2.18.g','补集','complement','E 在 X 中的补集是 Eᶜ={p∈X:p∉E}。'),
('2.18.h','完美集','perfect set','E 是完美集，当且仅当 E 是闭集，且 E 的每个点都是 E 的聚点。'),
('2.18.i','有界集','bounded set','E⊂X 有界，是指存在实数 M 和 q∈X，使所有 p∈E 都有 d(p,q)<M。'),
('2.18.j','稠密集','dense set','E 在 X 中稠密，当且仅当 X 中每个点都是 E 的聚点或属于 E。'),
('2.19','邻域是开集','neighborhood open','度量空间中，每个邻域 Nᵣ(p) 都是开集。'),
('2.20','聚点邻域含无穷多点','limit point infinite','若 p 是 E 的聚点，则 p 的每个邻域都包含 E 的无穷多个点。'),
('2.23','开闭集的补集关系','open closed complement','E 是开集当且仅当 Eᶜ 是闭集；等价地，F 是闭集当且仅当 Fᶜ 是开集。'),
('2.24','开闭集的并交','union intersection open closed','任意开集的并是开集；任意闭集的交是闭集；有限个开集的交是开集；有限个闭集的并是闭集。'),
('2.26','闭包','closure','设 E′ 是 E 的全部聚点组成的集合。E 的闭包定义为 E̅=E∪E′。'),
('2.31','开覆盖','open cover','度量空间 X 中，若一族开集 {Gα} 满足 E⊂⋃αGα，则称它为 E 的开覆盖。'),
('2.32','紧致集','compact compactness 紧集 紧性','K⊂X 紧致，当且仅当 K 的每个开覆盖都存在有限子覆盖：能从覆盖中选出有限个开集，其并仍覆盖 K。'),
('2.34','紧集是闭集','compact closed','度量空间的紧致子集都是闭集。'),
('2.35','紧集的闭子集仍紧','closed subset compact','若 K 是度量空间 X 中的紧集，F⊂K 且 F 在 X 中闭，则 F 紧致。'),
('2.36','紧集族的有限交性质','finite intersection property','若非空的一族紧集 {Kα} 的每个有限子族都有非空交集，则全族交集 ⋂αKα 非空。'),
('2.37','紧集的无穷子集有聚点','compact infinite limit point','若 K 紧致，E⊂K 是无穷集，则 E 至少有一个属于 K 的聚点。'),
('2.40','欧氏空间的闭矩体紧致','k-cell compact','ℝᵏ 中每个 k-cell（各坐标属于有限闭区间的矩体）都是紧集。'),
('2.41','Heine–Borel 定理','Heine Borel closed bounded compact','对 E⊂ℝᵏ，下列等价：① E 闭且有界；② E 紧致；③ E 的每个无穷子集都有属于 E 的聚点。闭且有界⇒紧致的方向不能直接推广到任意度量空间。'),
('2.42','Weierstrass 聚点定理','Bolzano Weierstrass bounded infinite','ℝᵏ 中每个有界无穷子集都有一个属于 ℝᵏ 的聚点。'),
('3.1','序列收敛','sequence convergence limit','度量空间 X 中，序列 (pₙ) 收敛到 p∈X，是指对每个 ε>0，存在整数 N，使 n≥N 时 d(pₙ,p)<ε。'),
('3.2','收敛序列的基本性质','unique limit bounded sequence','度量空间中的收敛序列有唯一极限且有界。若 p 是集合 E 的聚点，则存在 E 中的序列收敛到 p。'),
('3.5','子序列','subsequence','若正整数 n₁<n₂<⋯，则 (pₙᵢ) 是 (pₙ) 的子序列。收敛子序列的极限称为原序列的子序列极限。'),
('3.6','紧空间的子序列收敛性','sequential compactness bounded sequence','紧度量空间 X 中每个序列都有子序列收敛到 X 中的点；特别地，ℝᵏ 中每个有界序列都有收敛子序列。'),
('3.8','Cauchy 序列','Cauchy sequence 柯西序列','度量空间 X 中，(pₙ) 是 Cauchy 序列，当且仅当对每个 ε>0，存在整数 N，使所有 n,m≥N 都有 d(pₙ,pₘ)<ε。'),
('3.11','收敛与 Cauchy 序列','Cauchy convergence compact Euclidean','① 每个收敛序列都是 Cauchy 序列；② 紧度量空间中的每个 Cauchy 序列都收敛；③ ℝᵏ 中的每个 Cauchy 序列都收敛。'),
('4.1','函数极限','function limit','设 E⊂X，f:E→Y，p 是 E 的聚点。f(x)→q (x→p)，是指对每个 ε>0，存在 δ>0，使 x∈E 且 0<dX(x,p)<δ 时 dY(f(x),q)<ε。'),
('4.5','连续性','continuity continuous','设 f:E⊂X→Y，p∈E。f 在 p 连续，当且仅当对每个 ε>0，存在 δ>0，使所有 x∈E 满足 dX(x,p)<δ 时，dY(f(x),f(p))<ε。'),
('4.8','连续性的开集刻画','preimage open continuity','映射 f:X→Y 连续，当且仅当 Y 中每个开集的原像在 X 中是开集。'),
('4.14','紧集的连续像紧致','continuous image compact','若 X 是紧度量空间，f:X→Y 连续，Y 是度量空间，则 f(X) 紧致。'),
('4.15','连续像的闭性与有界性','continuous compact bounded closed','若 X 是紧度量空间，f:X→ℝᵏ 连续，则 f(X) 闭且有界；特别地，f 有界。'),
('4.16','极值定理','extreme value maximum minimum','设 X 是非空紧度量空间，f:X→ℝ 连续。则 f 在 X 上取得最大值与最小值，即存在 p,q∈X，使 f(q)≤f(x)≤f(p) 对所有 x∈X 成立。'),
('4.18','一致连续','uniform continuity','f:X→Y 一致连续，是指对每个 ε>0，存在 δ>0，使所有 p,q∈X 只要 dX(p,q)<δ，就有 dY(f(p),f(q))<ε。δ 不能依赖于 p 或 q。'),
('4.19','紧空间上的连续映射一致连续','Heine Cantor uniform continuity','若 X 是紧度量空间，f:X→Y 连续，Y 是度量空间，则 f 在 X 上一致连续。'),
('5.1','导数','derivative differentiable','实函数 f 定义在 [a,b] 上。在 x 处，若差商 (f(t)−f(x))/(t−x) 在 t→x 时有有限极限，则称此极限为 f′(x)，并称 f 在 x 可微；端点采用定义域内的单侧极限。'),
('5.2','可微蕴含连续','differentiability continuity','若实函数 f 在 [a,b] 的点 x 处可微，则 f 在 x 连续。'),
('5.10','中值定理','mean value theorem','若实函数 f 在 [a,b] 上连续，且在 (a,b) 上可微，则存在 ξ∈(a,b)，使 f(b)−f(a)=(b−a)f′(ξ)。'),
('7.7','一致收敛','uniform convergence','函数列 fₙ 在 E 上一致收敛到 f，是指对每个 ε>0，存在 N，使所有 n≥N 和所有 x∈E 都有 |fₙ(x)−f(x)|<ε。N 不能依赖于 x。'),
('7.8','一致收敛的 Cauchy 判据','uniform Cauchy criterion','复值函数列 fₙ 在 E 上一致收敛，当且仅当对每个 ε>0，存在 N，使所有 m,n≥N 和 x∈E 都有 |fₙ(x)−fₘ(x)|<ε。'),
('7.12','一致极限保持连续','uniform limit continuous','若函数列 fₙ 在度量空间的集合 E 上连续，且在 E 上一致收敛到 f，则 f 在 E 上连续。'),
('7.13','Dini 定理','Dini monotone compact','设 K 紧致，fₙ 是 K 上的连续实函数，逐点收敛到连续函数 f，且对所有 x∈K、n≥1 有 fₙ(x)≥fₙ₊₁(x)。则 fₙ→f 在 K 上一致收敛。'),
('7.16','一致收敛与积分交换','uniform convergence integration','设 α 在 [a,b] 上单调递增，每个 fₙ 在 [a,b] 上 Riemann–Stieltjes 可积，且 fₙ→f 一致。则 f 也可积，且 ∫f dα=limₙ∫fₙ dα。'),
('7.17','导数列一致收敛定理','uniform convergence differentiation','设 fₙ 在 [a,b] 上可微，对某个 x₀∈[a,b] 数列 fₙ(x₀) 收敛，且导数列 fₙ′ 在 [a,b] 上一致收敛。则 fₙ 在 [a,b] 上一致收敛到可微函数 f，并且 f′(x)=limₙ fₙ′(x)。')]
nodes=[]
for id,title,aliases,statement in rows:
 ref='.'.join(id.split('.')[:2]); source=lookup[ref]
 n=dict(source,id=id,title=title,aliases=aliases.split(),statement=statement,status='reviewed',intuition='中文学习表述；可通过原文按钮核对教材。')
 if id!=ref: n['kind']='definition'
 nodes.append(n)
# Direction: theorem/concept → required concept/result. Review evidence is an explanatory
# note based on the cited original entry, not a claim of verbatim quotation.
edges=[]
def edge(a,b,relation='uses_definition',note=None):
 edges.append({'source':a,'target':b,'relation':relation,'status':'reviewed','evidence':note or f'按 Rudin {a.split(".")[0]}.{a.split(".")[1]} 的表述核对：该条目使用「{next((n["title"] for n in nodes if n["id"]==b),b)}」。'})
for a,bs in {
'1.8':['1.7'],'1.10':['1.8'],'1.19':['1.10'],
'2.18.a':['2.15'],'2.18.b':['2.18.a'],'2.18.c':['2.18.b'],'2.18.d':['2.18.b'],'2.18.e':['2.18.a'],'2.18.f':['2.18.e'],'2.18.h':['2.18.d','2.18.b'],'2.18.i':['2.15'],'2.18.j':['2.18.b'],
'2.19':['2.18.a','2.18.f'],'2.20':['2.18.b'],'2.23':['2.18.d','2.18.f','2.18.g'],'2.24':['2.18.d','2.18.f'],'2.26':['2.18.b'],
'2.31':['2.18.f'],'2.32':['2.31'],'2.34':['2.32','2.18.d'],'2.35':['2.32','2.18.d'],'2.36':['2.32'],'2.37':['2.32','2.18.b'],'2.40':['2.32'],'2.41':['2.32','2.18.d','2.18.i'],'2.42':['2.18.i','2.18.b'],
'3.1':['2.15'],'3.2':['3.1'],'3.5':['3.1'],'3.6':['3.5','2.32'],'3.8':['2.15'],'3.11':['3.8','3.1','2.32'],
'4.1':['2.15','2.18.b'],'4.5':['2.15'],'4.8':['4.5','2.18.f'],'4.14':['4.5','2.32'],'4.15':['4.5','2.18.d','2.18.i'],'4.16':['4.5','2.32'],'4.18':['2.15'],'4.19':['4.5','4.18','2.32'],
'5.1':['4.1'],'5.2':['5.1','4.5'],'5.10':['5.1','4.5'],
'7.7':['3.1'],'7.8':['7.7','3.8'],'7.12':['7.7','4.5'],'7.13':['7.7','4.5','2.32'],'7.16':['7.7','6.2'],'7.17':['7.7','5.1','3.1']}.items():
 for b in bs: edge(a,b)
for a,bs in {'2.34':['2.23'],'2.41':['2.40','2.35','2.37'],'2.42':['2.40','2.37'],'3.6':['2.37','2.20','2.41'],'4.14':['4.8'],'4.15':['4.14','2.34','2.41'],'4.16':['4.15'],'7.12':['7.11'],'7.13':['4.8','2.35','2.36'],'7.17':['5.19','7.8']}.items():
 for b in bs: edge(a,b,'depends_on',f'教材 {a} 的证明使用 {b}；点击原文核对证明中的调用。')
(ROOT/'data/curated.json').write_text(json.dumps({'nodes':nodes,'edges':edges},ensure_ascii=False,indent=2),'utf8')
print('Source entries',len(index['nodes']),'explicit reference edges',len(index['edges']),'curated points',len(nodes),'curated relationships',len(edges))
