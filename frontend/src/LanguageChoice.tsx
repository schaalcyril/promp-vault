import {useId} from 'react';
export default function LanguageChoice({value,onChange,disabled=false,label='Langue du contenu'}:{value:string;onChange:(value:string)=>void;disabled?:boolean;label?:string}){
 const name=useId();
 return <fieldset className="language-choice" disabled={disabled}><legend>{label}</legend><div className="language-options">{[['auto','Automatique (FR / EN)'],['fr','Français'],['en','Anglais']].map(([code,title])=><label key={code} className={value===code?'selected':''}><input type="radio" name={name} value={code} checked={value===code} onChange={()=>onChange(code)}/><span>{title}</span></label>)}</div></fieldset>;
}
