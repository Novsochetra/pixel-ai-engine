import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NEW_UPLOAD } from './animate-server';
import { RUNNING, renderApp } from './render-app';
import { postedBody, rotateServer, startState } from './rotate-server';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const inspector = () => screen.getByRole('complementary', { name: 'Inspector' });

const rotateButton = () => screen.getByRole('button', { name: /^(Rotate|Job running)$/ });

const field = (label: string | RegExp) => within(inspector()).getByLabelText(label);

const openSheet = () =>
  screen.getAllByRole('dialog', { hidden: true }).find((dialog) => dialog.hasAttribute('open'))!;

async function formLoaded() {
  await within(inspector()).findByLabelText('Turn with');
}

describe('the rotate form', () => {
  it('turns with the model the LoRA learnt on, unless another is picked', async () => {
    const server = rotateServer(startState());
    renderApp('/rotate', server);
    await formLoaded();

    expect(field('Turning model')).toHaveProperty('value', 'flux2-klein-base-4b');
    await userEvent.selectOptions(field('Turning model'), 'flux2-klein-4b');
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    await vi.waitFor(() => expect(postedBody(server)?.turningModel).toBe('flux2-klein-4b'));
  });

  it('posts the front view, LoRA, model, sprite and views', async () => {
    const server = rotateServer(startState());
    renderApp('/rotate', server);
    await formLoaded();

    expect(within(inspector()).getByRole('img', { name: 'a lava dragon, front' })).toBeTruthy();
    await userEvent.selectOptions(field('Turn with'), 'runs/rotate-v2/checkpoints/step-000500');
    await userEvent.selectOptions(field('Turning model'), 'flux2-klein-base-4b');
    await userEvent.selectOptions(field('Sprite size'), '64');
    await userEvent.click(field('Back'));
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');

    await vi.waitFor(() => expect(postedBody(server)).toBeDefined());
    expect(postedBody(server)).toEqual({
      source: 'generated/dragon/s0',
      lora: 'runs/rotate-v2/checkpoints/step-000500',
      turningModel: 'flux2-klein-base-4b',
      sprite: '64',
      views: ['left', 'right'],
    });
  });

  it('offers only characters with a front view, and turns an upload', async () => {
    const server = rotateServer(startState());
    renderApp('/rotate', server);
    await formLoaded();

    const made = [...(field('Generated character') as HTMLSelectElement).options];
    expect(made.map((option) => option.value)).toEqual(['generated/dragon/s0']);

    await userEvent.click(within(inspector()).getByRole('button', { name: 'Uploaded' }));
    await userEvent.upload(
      field('PNG to upload'),
      new File(['png'], 'slime.png', { type: 'image/png' }),
    );
    await vi.waitFor(() =>
      expect((field('Uploaded picture') as HTMLSelectElement).value).toBe(NEW_UPLOAD.value),
    );
    await userEvent.click(rotateButton());

    await vi.waitFor(() => expect(postedBody(server)?.source).toBe(NEW_UPLOAD.value));
  });

  it('says what is missing before Rotate', async () => {
    const server = rotateServer({ ...startState(), loras: [] });
    renderApp('/rotate', server);
    await formLoaded();

    const reason = 'Train a rotate LoRA first, on the Training screen.';
    expect(within(inspector()).getByText(reason)).toBeTruthy();
    expect((rotateButton() as HTMLButtonElement).disabled).toBe(true);
    await userEvent.keyboard('{Meta>}{Enter}{/Meta}');
    expect(postedBody(server)).toBeUndefined();
  });

  it('shows a refused form in words, until it is closed', async () => {
    const detail = 'Pick a rotate LoRA from the list.';
    renderApp('/rotate', rotateServer({ ...startState(), refusal: { status: 400, detail } }));
    await formLoaded();

    await userEvent.click(rotateButton());

    const alert = await within(inspector()).findByRole('alert');
    expect(alert.textContent).toContain(detail);
    await userEvent.click(within(alert).getByRole('button', { name: 'Close the error' }));
    expect(within(inspector()).queryByRole('alert')).toBeNull();
  });

  it('waits while a job runs', async () => {
    const server = rotateServer({ ...startState(), job: RUNNING });
    renderApp('/rotate', server);
    await formLoaded();

    await vi.waitFor(() => expect(rotateButton().textContent).toBe('Job running'));
    expect((rotateButton() as HTMLButtonElement).disabled).toBe(true);
  });
});

describe('the rotate content', () => {
  it('shows each turned character as a tile that turns under the pointer, opening large', async () => {
    renderApp('/rotate', rotateServer(startState()));

    const list = await screen.findByRole('list', { name: 'Turned characters' });
    const tiles = [...list.querySelectorAll<HTMLElement>('.made-tile')];
    const shownView = () => within(tiles[0]!).getByRole('img').getAttribute('alt');
    expect(tiles.map((tile) => tile.textContent)).toEqual([
      expect.stringContaining('Turned from dragon'),
      expect.stringContaining('Made and turned in Create'),
    ]);
    expect(shownView()).toBe('a lava dragon, Front');

    await userEvent.hover(tiles[0]!);
    await vi.waitFor(() => expect(shownView()).toBe('a lava dragon, Left'));
    await userEvent.unhover(tiles[0]!);
    expect(shownView()).toBe('a lava dragon, Front');

    await userEvent.click(tiles[0]!.querySelector<HTMLElement>('.made-tile__open')!);
    expect(within(openSheet()).getByRole('group', { name: 'Views' })).toBeTruthy();
    expect(within(openSheet()).getByText('s0 of 20261126-090000-turned-dragon')).toBeTruthy();
  });

  it('says what to do when nothing is turned yet', async () => {
    renderApp('/rotate', rotateServer({ ...startState(), turned: [] }));

    expect(await screen.findByText('Nothing turned yet')).toBeTruthy();
  });

  it('shows only the rotations of a try-out run, to compare with', async () => {
    renderApp('/rotate', rotateServer(startState()));
    await screen.findByRole('list', { name: 'Turned characters' });

    await userEvent.click(screen.getByRole('button', { name: 'Try-outs' }));

    expect(await screen.findByRole('region', { name: 'pac/val/3 → back' })).toBeTruthy();
    expect(screen.queryByRole('region', { name: 'pixel art of a knight' })).toBeNull();
    expect(screen.getByLabelText('Run')).toBeTruthy();
  });
});
