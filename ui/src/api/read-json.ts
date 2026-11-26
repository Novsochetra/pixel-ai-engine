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

export async function postJson<Reply>(url: string, body: object): Promise<Reply> {
  const reply = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!reply.ok) {
    throw await refusal(reply);
  }

  return reply.json();
}
