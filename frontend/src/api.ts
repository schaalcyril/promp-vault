export let appConfig={default_language:'auto',max_text_mib:10};
export async function loadConfig(){const response=await fetch('/api/config');if(!response.ok)throw new Error('Configuration indisponible');appConfig=await response.json();}
