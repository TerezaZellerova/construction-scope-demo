import { defineConfig,loadEnv } from 'vite';
export default defineConfig(({mode})=>{
 const env=loadEnv(mode,process.cwd(),'');
 const api=env.VITE_API_URL;
 if(env.VERCEL==='1' && (!api || !api.startsWith('https://')))throw new Error('Vercel requires HTTPS VITE_API_URL');
 if(api){const url=new URL(api);if(url.username||url.password||url.search||url.hash||url.pathname!=='/')throw new Error('VITE_API_URL must be an origin without credentials');}
 return {server:{proxy:{'/api':'http://127.0.0.1:8000'}},build:{sourcemap:false}};
});
