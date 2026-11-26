export async function readJson<Reply>(reply: Response): Promise<Reply> {
  if (!reply.ok) {
    throw new Error(`The server answered ${reply.status}.`);
  }

  return reply.json();
}

export const getJson = <Reply>(url: string) => fetch(url).then(readJson<Reply>);

// A refused form comes back with the reason in `detail`, written for the person who sent it.
async function refusal(reply: Response): Promise<Error> {
  const body = await reply.json().catch(() => null);
  const detail = body?.detail;

  return new Error(typeof detail === 'string' ? detail : `The server answered ${reply.status}.`);
}

async function post<Reply>(url: string, body: BodyInit, contentType: string): Promise<Reply> {
  const reply = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': contentType },
    body,
  });

  if (!reply.ok) {
    throw await refusal(reply);
  }

  return reply.json();
}

export const postJson = <Reply>(url: string, body: object) =>
  post<Reply>(url, JSON.stringify(body), 'application/json');

export const postFile = <Reply>(url: string, file: Blob) => post<Reply>(url, file, file.type);
