import type {Session} from './session';
type Report=ReturnType<Session['restorationReport']>;
export default function RestorationSummary({report,hasReply}:{report:Report;hasReply:boolean}){
 const labels={secret:'Secret maintenu masqué',unknown:'Marqueur inconnu de cette session',suspected:'Marqueur possiblement altéré'};
 return <section className="restoration-summary" aria-labelledby="restoration-heading"><div className="panel-title"><h2 id="restoration-heading">Bilan de restauration</h2></div>
 {!hasReply?<p>Collez la réponse de l’IA pour voir ce qui peut être restauré.</p>:<>
 <dl className="restoration-counts" aria-live="polite"><div><dt>Occurrences restaurées</dt><dd>{report.restored}</dd></div><div><dt>Secrets laissés masqués</dt><dd>{report.secrets}</dd></div><div><dt>Marqueurs inconnus</dt><dd>{report.unknown}</dd></div><div><dt>Marqueurs à vérifier</dt><dd>{report.suspected}</dd></div></dl>
 {!report.hasMapping&&<p className="notice">Aucune correspondance dans cette session. Analysez d’abord le texte ici ; les correspondances sont perdues après un rechargement ou l’effacement de la session.</p>}
 {(report.unknown>0||report.suspected>0)&&<p className="notice">Restauration à vérifier : les marqueurs inconnus ou possiblement altérés restent inchangés. Aucune valeur n’est devinée. Corrigez la réponse à partir du texte protégé original si nécessaire.</p>}
 {report.restored+report.secrets+report.unknown+report.suspected===0&&<p>Aucun marqueur reconnu dans la réponse. Le texte reste inchangé ; cela ne garantit pas que l’IA a conservé les marqueurs.</p>}
 <p className="restoration-help">Comptage par occurrence, y compris les répétitions. La détection des marqueurs altérés est indicative. Les secrets ne sont jamais restaurés.</p>
 {report.issues.length>0&&<details><summary>Voir les marqueurs laissés inchangés</summary><ul className="restoration-issues">{report.issues.map(issue=><li key={issue.kind+issue.marker}><strong>{labels[issue.kind]}</strong><code>{issue.marker}</code><span>× {issue.count}</span></li>)}</ul>{report.omitted>0&&<p>{report.omitted} occurrence(s) supplémentaire(s) non détaillée(s). Le bilan ci-dessus reste complet.</p>}</details>}
 </>}
 </section>;
}
