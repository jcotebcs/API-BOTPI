import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - rich is optional
    RICH_AVAILABLE = False
    print("⚠️  Rich not available. Install with: pip install rich")

from api_bot.core.discovery_bot import ComprehensiveAPIBot
from api_bot.core.key_manager import SecureAPIKeyManager

class CLI:
    """Command Line Interface for API Discovery Bot

    The class mirrors the interactive interface described in the project
    overview.  For the unit tests the methods can also be invoked directly so
    they aim to be side-effect free and to return useful information whenever
    possible.
    """
    def __init__(self):
        self.bot = ComprehensiveAPIBot()
        self.key_manager = SecureAPIKeyManager()
        self.console = Console() if RICH_AVAILABLE else None

    # ------------------------------------------------------------------
    # Helper printing utilities
    # ------------------------------------------------------------------
    def print(self, text, **kwargs):
        if self.console:
            self.console.print(text, **kwargs)
        else:  # pragma: no cover - simple console fallback
            print(text)

    # ------------------------------------------------------------------
    # Main loop helpers (used only when running interactively)
    # ------------------------------------------------------------------
    def print_banner(self):
        banner = """
    ╔═══════════════════════════════════════════════════╗
    ║              🤖 API Discovery Bot                 ║
    ║          Comprehensive API Search System          ║
    ╚═══════════════════════════════════════════════════╝
        """
        if self.console:
            self.console.print(Panel(banner.strip(), style="blue"))
        else:
            print(banner)

    def show_main_menu(self) -> str:
        menu = """
[bold blue]Main Menu:[/bold blue]
[green]1.[/green] 🔍 Search APIs
[green]2.[/green] 🔐 Manage API Keys  
[green]3.[/green] 📊 Show Statistics
[green]4.[/green] 🔄 Update Database
[green]5.[/green] ⚙️  Setup Database
[green]6.[/green] 💾 Export Results
[green]0.[/green] 🚪 Exit
        """
        self.print(menu)
        if RICH_AVAILABLE:
            return Prompt.ask("Choose an option", choices=["0", "1", "2", "3", "4", "5", "6"])
        return input("Choose an option (0-6): ")

    # ------------------------------------------------------------------
    # Search functionality
    # ------------------------------------------------------------------
    def search_apis(self):
        self.print("\n🔍 [bold]API Search[/bold]", style="blue")
        query = Prompt.ask("Enter search terms") if RICH_AVAILABLE else input("Enter search terms: ")
        if not query.strip():
            self.print("❌ Please enter search terms", style="red")
            return
        self.print(f"🔎 Searching for: '{query}'...")
        try:
            results = self.bot.comprehensive_search(query)
            formatted_results = self.bot.format_search_results(results, query)
            if self.console:
                self.console.print(Markdown(formatted_results))
            else:  # pragma: no cover
                print(formatted_results)
            self._show_detailed_api_info(results)
        except Exception as exc:  # pragma: no cover - runtime errors
            self.print(f"❌ Search error: {exc}", style="red")

    def _show_detailed_api_info(self, results):
        all_results = {}
        for _source, apis in results.items():
            for api in apis:
                all_results.setdefault(api['name'], api)
        if not all_results:
            return
        if RICH_AVAILABLE:
            show_details = Confirm.ask("\nWould you like to see detailed info for any API?")
        else:  # pragma: no cover
            show_details = input("\nWould you like to see detailed info for any API? (y/n): ").lower().startswith('y')
        if not show_details:
            return
        api_list = list(all_results.keys())
        if self.console:
            table = Table(title="Available APIs")
            table.add_column("Number", style="cyan")
            table.add_column("API Name", style="green")
            table.add_column("Category", style="yellow")
            for i, (name, api) in enumerate(all_results.items(), 1):
                table.add_row(str(i), name, api.get('category', 'Unknown'))
            self.console.print(table)
        else:  # pragma: no cover
            print("\nAvailable APIs:")
            for i, name in enumerate(api_list, 1):
                print(f"{i}. {name}")
        try:
            if RICH_AVAILABLE:
                choice = Prompt.ask("Enter API number", choices=[str(i) for i in range(1, len(api_list) + 1)])
            else:  # pragma: no cover
                choice = input(f"Enter API number (1-{len(api_list)}): ")
            api_index = int(choice) - 1
            selected_api = list(all_results.values())[api_index]
            self._display_api_details(selected_api)
        except (ValueError, IndexError):  # pragma: no cover - invalid user input
            self.print("❌ Invalid selection", style="red")

    def _display_api_details(self, api):
        details = f"""
# 📋 Detailed API Information

## {api['name']}

**🏠 Host:** {api['host']}
**🏢 Provider:** {api.get('manufacturer', 'Unknown')}
**📂 Category:** {api.get('category', 'Unknown')}

**📝 Description:**
{api['description']}

**🔐 Authentication:** {api.get('auth_type', 'Unknown')}
**💰 Pricing:** {api.get('pricing', 'Not specified')}
**⚡ Rate Limit:** {api.get('rate_limit', 'Not specified')}

**📚 Documentation:** {api.get('documentation', 'Not available')}
        """
        endpoints = self.bot.get_api_endpoints(api['id'])
        if endpoints:
            details += "\n**🛠️ Available Endpoints:**\n"
            for ep in endpoints:
                details += f"- `{ep['method']} {ep['path']}` - {ep['description']}\n"
        if self.console:
            self.console.print(Markdown(details))
        else:  # pragma: no cover
            print(details)

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------
    def manage_keys(self):
        self.print("\n🔐 [bold]API Key Management[/bold]", style="blue")
        while True:
            menu = """
[bold]Key Management Options:[/bold]
[green]1.[/green] 📝 Add/Update API Key
[green]2.[/green] 📋 List Stored Keys  
[green]3.[/green] 🔍 Check Key Health
[green]4.[/green] 🗑️  Delete Key
[green]5.[/green] 📊 Key Dashboard
[green]0.[/green] ⬅️  Back to Main Menu
            """
            self.print(menu)
            if RICH_AVAILABLE:
                choice = Prompt.ask("Choose an option", choices=["0", "1", "2", "3", "4", "5"])
            else:  # pragma: no cover
                choice = input("Choose an option (0-5): ")
            if choice == '0':
                break
            elif choice == '1':
                self._add_api_key()
            elif choice == '2':
                self._list_keys()
            elif choice == '3':
                self._check_key_health()
            elif choice == '4':
                self._delete_key()
            elif choice == '5':
                self._show_key_dashboard()

    def _add_api_key(self):
        service = Prompt.ask("Enter service name (e.g., 'stripe', 'twitter')") if RICH_AVAILABLE else input("Enter service name (e.g., 'stripe', 'twitter'): ")
        api_key = Prompt.ask("Enter API key", password=True) if RICH_AVAILABLE else input("Enter API key: ")
        try:
            self.key_manager.store_api_key(service, api_key)
            self.print(f"✅ API key for {service} stored successfully!", style="green")
        except Exception as exc:  # pragma: no cover - IO errors
            self.print(f"❌ Error storing key: {exc}", style="red")

    def _list_keys(self):
        try:
            keys = self.key_manager.list_stored_keys()
            if not keys:
                self.print("📭 No API keys stored", style="yellow")
                return
            if self.console:
                table = Table(title="Stored API Keys")
                table.add_column("Service", style="cyan")
                table.add_column("Created", style="green")
                table.add_column("Last Used", style="yellow")
                table.add_column("Usage Count", style="magenta")
                table.add_column("Status", style="red")
                for key in keys:
                    status = "✅ Active" if key.get('active', True) else "❌ Inactive"
                    table.add_row(
                        key['service'],
                        key.get('created', '')[:10] if key.get('created') else 'Unknown',
                        key.get('last_used', '')[:10] if key.get('last_used') else 'Never',
                        str(key.get('usage_count', 0)),
                        status,
                    )
                self.console.print(table)
            else:  # pragma: no cover
                print("\nStored API Keys:")
                for key in keys:
                    status = "Active" if key.get('active', True) else "Inactive"
                    print(f"- {key['service']}: Created {key.get('created', '')[:10]}, Used {key.get('usage_count', 0)} times ({status})")
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Error listing keys: {exc}", style="red")

    def _check_key_health(self):
        service = Prompt.ask("Enter service name to check") if RICH_AVAILABLE else input("Enter service name to check: ")
        try:
            health = self.key_manager.check_key_health(service)
            if health['status'] == 'healthy':
                self.print(f"✅ {service} key is healthy", style="green")
                self.print(f"   Last used: {health.get('last_used', 'Never')}")
                self.print(f"   Usage count: {health.get('usage_count', 0)}")
            elif health['status'] == 'inactive':
                self.print(f"⚠️  {service} key is inactive", style="yellow")
            else:
                self.print(f"⚠️  {service} key has issues: {health.get('message', 'Unknown error')}", style="yellow")
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Error checking key health: {exc}", style="red")

    def _delete_key(self):
        service = Prompt.ask("Enter service name to delete") if RICH_AVAILABLE else input("Enter service name to delete: ")
        confirm = Confirm.ask(f"Are you sure you want to delete the {service} API key?") if RICH_AVAILABLE else input(f"Are you sure you want to delete the {service} API key? (y/n): ").lower().startswith('y')
        if confirm:
            try:
                self.key_manager.delete_key(service)
                self.print(f"✅ {service} API key deleted", style="green")
            except Exception as exc:  # pragma: no cover
                self.print(f"❌ Error deleting key: {exc}", style="red")

    def _show_key_dashboard(self):
        try:
            from api_bot.core.key_manager import SecureAPIDiscoveryBot
            dashboard_bot = SecureAPIDiscoveryBot()
            dashboard = dashboard_bot.get_key_dashboard()
            if self.console:
                self.console.print(Panel(dashboard, title="API Key Dashboard"))
            else:  # pragma: no cover
                print(dashboard)
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Error showing dashboard: {exc}", style="red")

    # ------------------------------------------------------------------
    # Statistics and database operations
    # ------------------------------------------------------------------
    def show_stats(self):
        """Display statistics about the internal API catalogue."""
        self.print("\n📊 [bold]Database Statistics[/bold]", style="blue")
        try:
            stats = self.bot.get_stats()
            stats_text = f"""
**📊 Total APIs:** {stats['total_apis']}

**📂 By Category:**
"""
            for category, count in stats['by_category'].items():
                stats_text += f"   • {category.title()}: {count}\n"
            stats_text += """

**🔍 By Source:**
"""
            for source, count in stats['by_source'].items():
                stats_text += f"   • {source.replace('_', ' ').title()}: {count}\n"
            stats_text += f"""

**📈 Recent Activity:**
   • Searches this week: {stats.get('searches_last_week', 0)}
"""
            if self.console:
                self.console.print(Markdown(stats_text))
            else:  # pragma: no cover
                print(stats_text)
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Error retrieving stats: {exc}", style="red")

    def update_database(self):
        """Trigger a database update.

        In this simplified implementation the method merely calls the bot and
        reports success.
        """
        self.print("\n🔄 [bold]Updating Database[/bold]", style="blue")
        try:
            self.bot.update_database()
            self.print("✅ Database update complete", style="green")
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Update error: {exc}", style="red")

    def setup_database(self):
        """Perform one-time setup of the database."""
        self.print("\n⚙️  [bold]Setting Up Database[/bold]", style="blue")
        try:
            self.bot.setup_database()
            self.print("✅ Database setup complete", style="green")
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Setup error: {exc}", style="red")

    def export_results(self):
        """Export the current API catalogue to a JSON file."""
        self.print("\n💾 [bold]Export Results[/bold]", style="blue")
        if RICH_AVAILABLE:
            filepath = Prompt.ask("Enter export file path", default="apis.json")
        else:  # pragma: no cover
            filepath = input("Enter export file path (default apis.json): ") or "apis.json"
        try:
            path = self.bot.export_results(filepath)
            self.print(f"✅ Results exported to {path}", style="green")
        except Exception as exc:  # pragma: no cover
            self.print(f"❌ Export error: {exc}", style="red")
