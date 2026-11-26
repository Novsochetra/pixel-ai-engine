export async function readJson<Reply>(reply: Response): Promise<Reply> {
  if (!reply.ok) {
    throw new Error(`The server answered ${reply.status}.`);
  }

  return reply.json();
}

export const getJson = <Reply>(url: string) => fetch(url).then(readJson<Reply>);
