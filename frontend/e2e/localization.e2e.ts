import { expect, test, type Page } from '@playwright/test';

async function signIn(page: Page) {
	await page.goto('/login');
	await page.getByLabel('Email', { exact: true }).fill('browser@example.test');
	await page.getByLabel('Password', { exact: true }).fill('test-browser-password-982');
	await page.getByRole('button', { name: 'Sign in', exact: true }).click();
}

test('persist the account language across browser sessions and a paired kiosk', async ({
	browser,
	page
}) => {
	test.setTimeout(60_000);
	const deviceContext = await browser.newContext();
	const otherContext = await browser.newContext();
	const device = await deviceContext.newPage();
	const other = await otherContext.newPage();
	await signIn(page);
	await expect(page.getByRole('heading', { name: 'Your day' })).toBeVisible();
	try {
		await page.getByRole('link', { name: 'Settings' }).click();
		await page.getByRole('combobox', { name: 'Language', exact: true }).selectOption('pt-BR');
		await page.getByRole('button', { name: 'Save preferences' }).click();
		await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');
		await expect(page.getByRole('heading', { name: 'Preferências' })).toBeVisible();
		await expect(page.getByText('Preferências salvas.')).toBeVisible();
		await page.reload();
		await expect(page.getByRole('combobox', { name: 'Idioma' })).toHaveValue('pt-BR');

		const timezone = page.getByLabel('Fuso horário');
		const tz = await timezone.inputValue();
		await timezone.fill('Invalid/Zone');
		await page.getByRole('button', { name: 'Salvar preferências' }).click();
		await expect(page.getByRole('alert')).toHaveText(
			'Use um fuso horário IANA, como America/Sao_Paulo.'
		);
		await expect(timezone).toHaveAttribute('aria-describedby', 'settings-error');
		await timezone.fill(tz);

		await signIn(other);
		await expect(other.locator('html')).toHaveAttribute('lang', 'pt-BR');
		await expect(other.getByRole('heading', { name: 'Seu dia' })).toBeVisible();
		await expect(other.getByRole('heading', { name: 'Design review' })).toBeVisible();
		await other.getByRole('button', { name: 'Nova tarefa' }).click();
		await expect(other.getByRole('dialog').getByLabel('Título')).toBeVisible();
		await other.getByRole('button', { name: 'Fechar editor' }).click();
		await other.goto('/api/v1/integrations/oauth/notion/callback/?state=expired');
		await expect(other).toHaveURL(/connections\?error=connection_expired$/);
		await expect(other.getByRole('alert')).toHaveText(
			'Esta solicitação de conexão expirou ou já foi usada. Comece de novo.'
		);
		await other.getByRole('button', { name: 'Sair', exact: true }).click();
		await other.getByLabel('E-mail', { exact: true }).fill('browser@example.test');
		await other.getByLabel('Senha', { exact: true }).fill('wrong-password');
		await other.getByRole('button', { name: 'Entrar', exact: true }).click();
		await expect(other.getByRole('alert')).toHaveText('O e-mail ou a senha está incorreto.');

		await device.goto('/kiosk');
		const code = device.locator('.pairing h2');
		await expect(code).toHaveText(/^[A-Z2-9]{8}$/);
		await page.getByLabel('Código de pareamento').fill((await code.textContent())!);
		await page.getByRole('button', { name: 'Aprovar tela' }).click();
		await expect(device.locator('html')).toHaveAttribute('lang', 'pt-BR', { timeout: 15_000 });
		await expect(device.getByText('TRABALHO DE HOJE')).toBeVisible();
		await expect(device.getByText('O resumo chegará em uma versão futura.')).toBeVisible();

		await page.getByRole('combobox', { name: 'Idioma' }).selectOption('es');
		await page.getByRole('button', { name: 'Salvar preferências' }).click();
		await expect(page.locator('html')).toHaveAttribute('lang', 'es');
		await expect(page.getByRole('heading', { name: 'Preferencias' })).toBeVisible();
		await device.reload();
		await expect(device.locator('html')).toHaveAttribute('lang', 'es');
		await expect(device.getByText('TRABAJO DE HOY')).toBeVisible();
		await device.evaluate(async () => {
			await navigator.serviceWorker.ready;
		});
		await deviceContext.setOffline(true);
		await device.reload({ waitUntil: 'domcontentloaded' });
		await expect(device.locator('html')).toHaveAttribute('lang', 'es');
		await expect(device.getByRole('status')).toContainText('SIN ACTUALIZAR');
		await expect(
			device.getByText('El resumen estará disponible en una versión futura.')
		).toBeVisible();
		await deviceContext.setOffline(false);

		await page.route('**/api/v1/integrations/connections/', (route) =>
			route.fulfill({ status: 503, json: { detail: 'Raw server message' } })
		);
		await page.getByRole('link', { name: 'Conexiones' }).click();
		await expect(page.getByRole('heading', { name: 'Conéctate a tu manera.' })).toBeVisible();
		await expect(page.getByRole('alert')).toHaveText('El servidor no está disponible.');
		await page.getByRole('navigation').getByRole('link', { name: 'Hoy', exact: true }).click();
		await expect(page.getByRole('heading', { name: 'Tu día' })).toBeVisible();
		await page.getByRole('button', { name: 'Nueva tarea' }).click();
		const dialog = page.getByRole('dialog');
		const title = dialog.getByLabel('Título');
		await title.fill('   ');
		await dialog.getByRole('button', { name: 'Guardar tarea' }).click();
		await expect(dialog.getByRole('alert')).toContainText('Rellena los campos obligatorios.');
		await expect(title).toHaveAttribute('aria-describedby', 'task-editor-error');
		await dialog.getByRole('button', { name: 'Cerrar editor' }).click();

		await page.getByRole('button', { name: 'Cerrar sesión' }).click();
		await expect(page.getByRole('heading', { name: 'Te damos la bienvenida.' })).toBeVisible();
		await page.getByLabel('Correo electrónico', { exact: true }).fill('browser@example.test');
		await page.getByLabel('Contraseña', { exact: true }).fill('test-browser-password-982');
		await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
		await expect(page.getByRole('heading', { name: 'Tu día' })).toBeVisible();

		await page.getByRole('link', { name: 'Configuración' }).click();
		await page.getByRole('combobox', { name: 'Idioma' }).selectOption('en');
		await page.getByRole('button', { name: 'Guardar preferencias' }).click();
		await expect(page.locator('html')).toHaveAttribute('lang', 'en');
		await device.reload();
		await expect(device.locator('html')).toHaveAttribute('lang', 'en');
		await expect(device.getByText('TODAY’S WORK')).toBeVisible();
	} finally {
		try {
			const csrfResponse = await page.request.get('/api/v1/csrf/', { timeout: 3000 });
			const body = (await csrfResponse.json()) as { csrf_token: string };
			await page.request.patch('/api/v1/settings/', {
				headers: { 'X-CSRFToken': body.csrf_token },
				data: { language: 'en' },
				timeout: 3000
			});
		} finally {
			await otherContext.close();
			await deviceContext.close();
		}
	}
});
