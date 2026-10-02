// Restricted grammar and exact rational arithmetic. No eval or executable input.
function gcd(a,b){a=a<0n?-a:a;while(b){[a,b]=[b,a%b];}return a;}
function rat(n,d=1n){if(d===0n)throw Error('除数不能为零');if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return [n/g,d/g];}
function op(a,b,s){const [n,d]=a,[m,e]=b;return s==='+'?rat(n*e+m*d,d*e):s==='-'?rat(n*e-m*d,d*e):s==='*'?rat(n*m,d*e):rat(n*e,d*m);}
function format([n,d]){
  if(n===0n)return '0';const neg=n<0n;n=neg?-n:n;
  let exponent=n.toString().length-d.toString().length;
  if(exponent>=0?n<d*10n**BigInt(exponent):n*10n**BigInt(-exponent)<d)exponent--;
  if(exponent>1000||exponent< -1000)throw Error('结果超出支持范围');
  const scale=27-exponent;
  const numerator=scale>=0?n*10n**BigInt(scale):n;
  const denominator=scale>=0?d:d*10n**BigInt(-scale);
  let q=numerator/denominator;const rem=numerator%denominator;
  if(rem*2n>denominator||(rem*2n===denominator&&q%2n))q++;
  let text=q.toString();
  if(scale>0){text=text.padStart(scale+1,'0');text=text.slice(0,-scale)+'.'+text.slice(-scale);text=text.replace(/0+$/,'').replace(/\.$/,'');}
  else text+='0'.repeat(-scale);
  return (neg?'-':'')+text;
}
export function calculate(expression){
  if(typeof expression!=='string'||!expression.trim())throw Error('请输入表达式');
  if(expression.length>500)throw Error('表达式最多 500 个字符');
  const tokens=expression.replaceAll('×','*').replaceAll('÷','/').match(/(?:\d+(?:\.\d*)?|\.\d+)|[+*/()\-]|\S/g)||[];let p=0;
  const peek=()=>tokens[p];
  function factor(depth){if(depth>64)throw Error('表达式嵌套过深');const t=tokens[p++];if(t==='+'||t==='-'){const [n,d]=factor(depth+1);return [t==='-'?-n:n,d];}if(t==='('){const v=expr(depth+1);if(tokens[p++]!==')')throw Error('括号不匹配');return v;}if(!t||! /^(?:\d+(?:\.\d*)?|\.\d+)$/.test(t))throw Error('表达式格式错误');const parts=t.split('.');return rat(BigInt((parts[0]||'0')+(parts[1]||'')),10n**BigInt((parts[1]||'').length));}
  function term(depth){let v=factor(depth);while(peek()==='*'||peek()==='/'){const s=tokens[p++];v=op(v,factor(depth),s);}return v;}
  function expr(depth){let v=term(depth);while(peek()==='+'||peek()==='-'){const s=tokens[p++];v=op(v,term(depth),s);}return v;}
  const result=expr(0);if(p!==tokens.length)throw Error('表达式含多余符号或缺少运算符');return format(result);
}
