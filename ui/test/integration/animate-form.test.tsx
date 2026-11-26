import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { animateServer, NEW_UPLOAD, postedBody, postedTo, startState } from './animate-server';
import { RUNNING, renderApp } from './render-app';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const inspector = () => screen.getByRole('complementary', { name: 'Inspector' });

const animateButton = () => screen.getByRole('button', { name: /^(Animate|Job running)$/ });

const field = (label: string | RegExp) => within(inspector()).getByLabelText(label);

async function formLoaded() {
  await within(inspector()).findByLabelText('Generated character');
}

describe('the animate form', () => {
  it('posts the chosen character, views, actions and video', async () => {
    const server = animateServer(startState());
    renderApp('/animate', server);
    await formLoaded();

    await userEvent.click(field('Left'));
    await userEvent.click(field('Right'));
    await userEvent.type(field(/^Actions, one a line/), '\n  Flaps  its wings\nwalk');
    await userEvent.selectOptions(field('Video size'), '512');
    await userEvent.click(animateButton());

    await vi.waitFor(() => expect(postedBody(server)).toBeDefined());
    expect(postedBody(server)).toEqual({
      source: 'generated/dragon/s0',
      subject: 'a lava dragon',
      views: ['front', 'left'],
      actions: 'idle\nwalk\nFlaps its wings',
      size: '512',
      frames: '33',
    });
  });

  it('offers only the views a character has, and says how long it takes', async () => {
    renderApp('/animate', animateServer(startState()));
    await formLoaded();

    await userEvent.selectOptions(field('Generated character'), 'generated/bird/s0');

    expect((field('Front') as HTMLInputElement).disabled).toBe(true);
    expect((field('Right') as HTMLInputElement).checked).toBe(true);
    expect((field(/^What it shows/) as HTMLTextAreaElement).value).toBe('a blue bird');
    expect(within(inspector()).getByText(/^2 clips, about 22 min/)).toBeTruthy();
  });

  it('uploads a PNG, then animates it with the words given', async () => {
    const server = animateServer(startState());
    renderApp('/animate', server);
    await formLoaded();

    await userEvent.click(within(inspector()).getByRole('button', { name: 'Uploaded' }));
    const png = new File(['png'], 'slime.png', { type: 'image/png' });
    await userEvent.upload(field('PNG to upload'), png);

    await vi.waitFor(() =>
      expect((field('Uploaded picture') as HTMLSelectElement).value).toBe(NEW_UPLOAD.value),
    );
    expect(postedTo(server, '/api/uploads')![0]).toBe('/api/uploads?name=slime.png');
    expect(animateButton().title).toBe('Say what the picture shows.');

    await userEvent.type(field(/^What it shows/), 'a green slime');
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    await vi.waitFor(() => expect(postedBody(server)?.source).toBe(NEW_UPLOAD.value));
    expect(postedBody(server).views).toEqual([]);
  });

  it('shows a refused upload in words, until it is closed', async () => {
    const detail = 'The file is not a PNG. Upload a PNG.';
    renderApp('/animate', animateServer({ ...startState(), uploadRefusal: detail }));
    await formLoaded();

    await userEvent.click(within(inspector()).getByRole('button', { name: 'Uploaded' }));
    await userEvent.upload(field('PNG to upload'), new File(['x'], 'a.png', { type: 'image/png' }));

    const alert = await within(inspector()).findByRole('alert');
    expect(alert.textContent).toContain(detail);
    await userEvent.click(within(alert).getByRole('button', { name: 'Close the error' }));
    expect(within(inspector()).queryByRole('alert')).toBeNull();
  });

  it('shows a refused form in words', async () => {
    const detail = 'Pick at least one view that s0 has: front, right.';
    renderApp('/animate', animateServer({ ...startState(), refusal: { status: 400, detail } }));
    await formLoaded();

    await userEvent.click(animateButton());

    expect((await within(inspector()).findByRole('alert')).textContent).toContain(detail);
  });

  it('says what is missing before Animate', async () => {
    const server = animateServer(startState());
    renderApp('/animate', server);
    await formLoaded();

    await userEvent.clear(field(/^Actions, one a line/));

    expect(
      within(inspector()).getByText('Say at least one action, for example: walk.'),
    ).toBeTruthy();
    expect((animateButton() as HTMLButtonElement).disabled).toBe(true);
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server)).toBeUndefined();
  });

  it('waits while a job runs, and says so', async () => {
    const server = animateServer({ ...startState(), job: RUNNING });
    renderApp('/animate', server);
    await formLoaded();

    await vi.waitFor(() => expect(animateButton().textContent).toBe('Job running'));
    expect((animateButton() as HTMLButtonElement).disabled).toBe(true);
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server)).toBeUndefined();
  });
});
