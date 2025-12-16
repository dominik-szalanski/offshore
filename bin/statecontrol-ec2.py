#!/usr/bin/env python3
"""
EC2 Instance State Control Script
Manages EC2 instances by ID or name across all AWS regions
"""

import sys
import argparse
import json
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import optional packages
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("Warning: boto3 not installed. Please install with: pip install boto3", file=sys.stderr)
    print("Or use the system package manager: pacman -S python-boto3", file=sys.stderr)
    sys.exit(1)

# Optional packages with fallbacks
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Define fallback color codes using ANSI escape sequences
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RESET = '\033[0m'
    
    class Style:
        RESET_ALL = '\033[0m'


class EC2Controller:
    """Controller for EC2 instance operations across all regions"""
    
    def __init__(self, profile: Optional[str] = None, verbose: bool = False):
        """
        Initialize EC2 controller
        
        Args:
            profile: AWS profile name to use
            verbose: Enable verbose output
        """
        self.profile = profile
        self.verbose = verbose
        self.session = self._create_session()
        self.regions = self._get_all_regions()
        
    def _create_session(self) -> boto3.Session:
        """Create boto3 session with specified profile"""
        try:
            if self.profile:
                return boto3.Session(profile_name=self.profile)
            return boto3.Session()
        except ProfileNotFound:
            self._error(f"AWS profile '{self.profile}' not found")
            sys.exit(1)
            
    def _get_all_regions(self) -> List[str]:
        """Get all available AWS regions"""
        try:
            ec2 = self.session.client('ec2', region_name='us-east-1')
            response = ec2.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            if self.verbose:
                self._info(f"Found {len(regions)} AWS regions")
            return regions
        except NoCredentialsError:
            self._error("AWS credentials not configured")
            self._warning("Please configure AWS CLI with: aws configure")
            self._warning("Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            sys.exit(1)
        except ClientError as e:
            self._error(f"Failed to get regions: {e}")
            # Fallback to common regions
            return [
                'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
                'ap-south-1', 'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2'
            ]
    
    def _info(self, message: str):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
    
    def _success(self, message: str):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def _warning(self, message: str):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    def _error(self, message: str):
        """Print error message"""
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    def _search_region(self, region: str, identifier: str) -> Optional[Dict]:
        """
        Search for instance in a specific region
        
        Args:
            region: AWS region to search
            identifier: Instance ID or name tag
            
        Returns:
            Instance information dict or None
        """
        try:
            ec2 = self.session.client('ec2', region_name=region)
            
            # Determine if identifier is instance ID or name
            if identifier.startswith('i-'):
                filters = [{'Name': 'instance-id', 'Values': [identifier]}]
            else:
                filters = [{'Name': 'tag:Name', 'Values': [identifier]}]
            
            response = ec2.describe_instances(Filters=filters)
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Get instance name from tags
                    name = None
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    return {
                        'region': region,
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'name': name,
                        'instance_type': instance.get('InstanceType'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'launch_time': instance.get('LaunchTime'),
                        'platform': instance.get('Platform', 'Linux'),
                        'architecture': instance.get('Architecture')
                    }
        except ClientError:
            # Region might not be accessible or instance not found
            pass
        return None
    
    def find_instance(self, identifier: str) -> Optional[Dict]:
        """
        Find instance across all regions
        
        Args:
            identifier: Instance ID or name tag
            
        Returns:
            Instance information dict or None
        """
        self._info(f"Searching for instance: {identifier}")
        
        # Use ThreadPoolExecutor for parallel region search
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._search_region, region, identifier): region
                for region in self.regions
            }
            
            for future in as_completed(futures):
                region = futures[future]
                if self.verbose:
                    self._info(f"Checking region: {region}")
                
                result = future.result()
                if result:
                    return result
        
        return None
    
    def list_instances(self, state_filter: Optional[str] = None) -> List[Dict]:
        """
        List all instances across all regions
        
        Args:
            state_filter: Optional state filter (running, stopped, etc.)
            
        Returns:
            List of instance information dicts
        """
        instances = []
        
        def list_region_instances(region: str) -> List[Dict]:
            """List instances in a specific region"""
            region_instances = []
            try:
                ec2 = self.session.client('ec2', region_name=region)
                
                filters = []
                if state_filter:
                    filters.append({'Name': 'instance-state-name', 'Values': [state_filter]})
                
                response = ec2.describe_instances(Filters=filters)
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        # Get instance name from tags
                        name = None
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        region_instances.append({
                            'region': region,
                            'instance_id': instance['InstanceId'],
                            'state': instance['State']['Name'],
                            'name': name or 'N/A',
                            'instance_type': instance.get('InstanceType', 'N/A'),
                            'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                            'public_ip': instance.get('PublicIpAddress', 'N/A')
                        })
            except ClientError:
                pass
            return region_instances
        
        # Use ThreadPoolExecutor for parallel region listing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(list_region_instances, region): region
                for region in self.regions
            }
            
            for future in as_completed(futures):
                region = futures[future]
                if self.verbose:
                    self._info(f"Listing instances in region: {region}")
                
                region_instances = future.result()
                instances.extend(region_instances)
        
        return instances
    
    def start_instance(self, instance_info: Dict, dry_run: bool = False) -> bool:
        """Start a stopped instance"""
        instance_id = instance_info['instance_id']
        region = instance_info['region']
        state = instance_info['state']
        
        if state != 'stopped':
            self._warning(f"Instance is not in stopped state (current: {state})")
            return False
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            self._info(f"Starting instance {instance_id}...")
            ec2.start_instances(InstanceIds=[instance_id], DryRun=dry_run)
            if not dry_run:
                self._success("Instance start initiated successfully")
            return True
        except ClientError as e:
            if 'DryRunOperation' in str(e):
                self._success("Dry run successful - instance would be started")
                return True
            self._error(f"Failed to start instance: {e}")
            return False
    
    def stop_instance(self, instance_info: Dict, force: bool = False, dry_run: bool = False) -> bool:
        """Stop a running instance"""
        instance_id = instance_info['instance_id']
        region = instance_info['region']
        state = instance_info['state']
        
        if not force and state != 'running':
            self._warning(f"Instance is not in running state (current: {state})")
            return False
        
        if force and state not in ['running', 'stopping']:
            self._warning(f"Instance is not in running or stopping state (current: {state})")
            return False
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            action = "Force stopping" if force else "Stopping"
            self._info(f"{action} instance {instance_id}...")
            ec2.stop_instances(InstanceIds=[instance_id], Force=force, DryRun=dry_run)
            if not dry_run:
                self._success(f"Instance {'force ' if force else ''}stop initiated successfully")
            return True
        except ClientError as e:
            if 'DryRunOperation' in str(e):
                self._success(f"Dry run successful - instance would be {'force ' if force else ''}stopped")
                return True
            self._error(f"Failed to stop instance: {e}")
            return False
    
    def reboot_instance(self, instance_info: Dict, dry_run: bool = False) -> bool:
        """Reboot a running instance"""
        instance_id = instance_info['instance_id']
        region = instance_info['region']
        state = instance_info['state']
        
        if state != 'running':
            self._warning(f"Instance must be running to reboot (current: {state})")
            return False
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            self._info(f"Rebooting instance {instance_id}...")
            ec2.reboot_instances(InstanceIds=[instance_id], DryRun=dry_run)
            if not dry_run:
                self._success("Instance reboot initiated successfully")
            return True
        except ClientError as e:
            if 'DryRunOperation' in str(e):
                self._success("Dry run successful - instance would be rebooted")
                return True
            self._error(f"Failed to reboot instance: {e}")
            return False
    
    def get_instance_status(self, instance_info: Dict) -> Dict:
        """Get detailed instance status"""
        instance_id = instance_info['instance_id']
        region = instance_info['region']
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            
            # Get instance status checks
            status_response = ec2.describe_instance_status(InstanceIds=[instance_id])
            
            status_info = {}
            if status_response['InstanceStatuses']:
                status = status_response['InstanceStatuses'][0]
                status_info['instance_status'] = status.get('InstanceStatus', {}).get('Status', 'N/A')
                status_info['system_status'] = status.get('SystemStatus', {}).get('Status', 'N/A')
            else:
                status_info['instance_status'] = 'N/A'
                status_info['system_status'] = 'N/A'
            
            return {**instance_info, **status_info}
        except ClientError as e:
            self._error(f"Failed to get instance status: {e}")
            return instance_info
    
    def change_instance_type(self, instance_info: Dict, new_type: str, dry_run: bool = False) -> bool:
        """Change instance type (instance must be stopped)"""
        instance_id = instance_info['instance_id']
        region = instance_info['region']
        state = instance_info['state']
        current_type = instance_info.get('instance_type', 'Unknown')
        
        if state != 'stopped':
            self._error(f"Instance must be stopped to change type (current state: {state})")
            self._warning("Stop the instance first with: stop command")
            return False
        
        if current_type == new_type:
            self._warning(f"Instance is already of type {new_type}")
            return True
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            self._info(f"Changing instance type from {current_type} to {new_type}...")
            
            ec2.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceType={'Value': new_type},
                DryRun=dry_run
            )
            
            if not dry_run:
                self._success(f"Instance type changed successfully from {current_type} to {new_type}")
                self._info("You can now start the instance with the new type")
            return True
        except ClientError as e:
            if 'DryRunOperation' in str(e):
                self._success(f"Dry run successful - instance type would be changed from {current_type} to {new_type}")
                return True
            elif 'InvalidInstanceType' in str(e):
                self._error(f"Invalid instance type: {new_type}")
                self._warning("Please check AWS documentation for valid instance types")
                return False
            elif 'InsufficientInstanceCapacity' in str(e):
                self._error(f"Insufficient capacity for instance type {new_type} in this region")
                self._warning("Try a different instance type or wait and retry")
                return False
            else:
                self._error(f"Failed to change instance type: {e}")
                return False
    
    def get_available_instance_types(self, region: str) -> List[str]:
        """Get list of available instance types in a region"""
        try:
            ec2 = self.session.client('ec2', region_name=region)
            # Get instance type offerings
            response = ec2.describe_instance_type_offerings(
                LocationType='region',
                Filters=[
                    {'Name': 'location', 'Values': [region]}
                ]
            )
            types = sorted(set([offering['InstanceType'] for offering in response['InstanceTypeOfferings']]))
            return types
        except ClientError:
            # Fallback to common instance types
            return [
                't3.nano', 't3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge', 't3.2xlarge',
                't3a.nano', 't3a.micro', 't3a.small', 't3a.medium', 't3a.large', 't3a.xlarge', 't3a.2xlarge',
                'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge',
                'c6i.large', 'c6i.xlarge', 'c6i.2xlarge', 'c6i.4xlarge', 'c6i.8xlarge',
                'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.8xlarge',
                'r5.large', 'r5.xlarge', 'r5.2xlarge', 'r5.4xlarge'
            ]


def format_table(rows: List[List], headers: List[str]) -> str:
    """Format data as a table (fallback for when tabulate is not available)"""
    if HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt='grid')
    
    # Simple table formatting without tabulate
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Create separator line
    separator = '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'
    
    # Format header
    header_line = '| ' + ' | '.join([str(h).ljust(w) for h, w in zip(headers, col_widths)]) + ' |'
    
    # Format rows
    formatted_rows = []
    for row in rows:
        row_line = '| ' + ' | '.join([str(cell).ljust(w) for cell, w in zip(row, col_widths)]) + ' |'
        formatted_rows.append(row_line)
    
    # Combine all parts
    result = [separator, header_line, separator]
    result.extend(formatted_rows)
    result.append(separator)
    
    return '\n'.join(result)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EC2 Instance State Control - Manage EC2 instances across all regions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start i-1234567890abcdef0
  %(prog)s stop my-web-server
  %(prog)s status production-db
  %(prog)s list
  %(prog)s list --state running
  %(prog)s resize my-server --type t3.large
  %(prog)s -p prod-account reboot webserver
  %(prog)s --dry-run stop test-instance
        """
    )
    
    parser.add_argument('command',
                       choices=['start', 'stop', 'force-stop', 'reboot', 'status', 'list', 'resize'],
                       help='Command to execute')
    parser.add_argument('instance', nargs='?',
                       help='Instance ID or name tag (not required for list command)')
    parser.add_argument('-p', '--profile',
                       help='AWS CLI profile to use')
    parser.add_argument('-n', '--dry-run', action='store_true',
                       help='Perform a dry run without making changes')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--state',
                       help='Filter instances by state (for list command)')
    parser.add_argument('--type',
                       help='New instance type (for resize command, e.g., t3.medium, c5.xlarge)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.command != 'list' and not args.instance:
        parser.error(f"'{args.command}' command requires an instance identifier")
    
    if args.command == 'resize' and not args.type:
        parser.error("'resize' command requires --type argument specifying the new instance type")
    
    # Create controller
    controller = EC2Controller(profile=args.profile, verbose=args.verbose)
    
    if args.dry_run:
        controller._warning("DRY RUN MODE - No changes will be made")
    
    # Execute command
    if args.command == 'list':
        instances = controller.list_instances(state_filter=args.state)
        if instances:
            # Sort by region and instance ID
            instances.sort(key=lambda x: (x['region'], x['instance_id']))
            
            # Display as table
            headers = ['Region', 'Instance ID', 'State', 'Name', 'Type', 'Private IP', 'Public IP']
            rows = [
                [i['region'], i['instance_id'], i['state'], i['name'], 
                 i['instance_type'], i['private_ip'], i['public_ip']]
                for i in instances
            ]
            print(format_table(rows, headers))
            controller._success(f"Found {len(instances)} instance(s)")
        else:
            controller._warning("No instances found")
    
    else:
        # Find the instance
        instance_info = controller.find_instance(args.instance)
        if not instance_info:
            controller._error(f"Instance '{args.instance}' not found in any AWS region")
            sys.exit(1)
        
        # Display instance information
        controller._success("Instance found:")
        print(f"  Region: {instance_info['region']}")
        print(f"  Instance ID: {instance_info['instance_id']}")
        print(f"  Name: {instance_info.get('name', 'N/A')}")
        print(f"  Current State: {instance_info['state']}")
        print(f"  Instance Type: {instance_info.get('instance_type', 'N/A')}")
        print(f"  Private IP: {instance_info.get('private_ip', 'N/A')}")
        print(f"  Public IP: {instance_info.get('public_ip', 'N/A')}")
        print()
        
        # Execute the command
        success = False
        if args.command == 'start':
            success = controller.start_instance(instance_info, dry_run=args.dry_run)
        elif args.command == 'stop':
            success = controller.stop_instance(instance_info, dry_run=args.dry_run)
        elif args.command == 'force-stop':
            success = controller.stop_instance(instance_info, force=True, dry_run=args.dry_run)
        elif args.command == 'reboot':
            success = controller.reboot_instance(instance_info, dry_run=args.dry_run)
        elif args.command == 'status':
            detailed_info = controller.get_instance_status(instance_info)
            print(f"  Platform: {detailed_info.get('platform', 'N/A')}")
            print(f"  Architecture: {detailed_info.get('architecture', 'N/A')}")
            print(f"  Launch Time: {detailed_info.get('launch_time', 'N/A')}")
            print(f"  Instance Status: {detailed_info.get('instance_status', 'N/A')}")
            print(f"  System Status: {detailed_info.get('system_status', 'N/A')}")
            success = True
        elif args.command == 'resize':
            success = controller.change_instance_type(instance_info, args.type, dry_run=args.dry_run)
        
        if args.dry_run:
            controller._warning("DRY RUN COMPLETE - No actual changes were made")
        
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)